from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from pathlib import Path
import json

from answer_deploy import answer_question  # fast pipeline for live chat

app = FastAPI()

# Browsers block cross origin calls unless the API says otherwise, and the
# deployed frontend is on a different domain from this API, so its origin has
# to be listed here explicitly.
ALLOWED_ORIGINS = [
    "http://localhost:3000",          # local dev server
    "https://nexara-rag.vercel.app",  # production frontend
]

# Vercel mints a fresh URL for every preview deployment, so those cannot be
# listed one by one. Starlette matches this against the whole origin string.
PREVIEW_ORIGIN_REGEX = r"https://nexara-[a-z0-9-]+\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=PREVIEW_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rolling log of live chat turns, kept next to this file rather than resolved
# against the working directory, so it lands in the same place either way.
CHAT_LOG_FILE = Path(__file__).with_name("chat_log.jsonl")
MAX_CHAT_LOG_ENTRIES = 50


class AskRequest(BaseModel):
    question: str
    # Earlier turns as {"role": "user"|"assistant", "content": str}. Defaults
    # to empty so an older client that omits the field still works.
    history: list[dict] = []


def read_chat_log() -> list[dict]:
    """
    Load the log oldest first. Bad lines are skipped rather than raising,
    since a half written line should not take down the endpoint.
    """
    if not CHAT_LOG_FILE.exists():
        return []

    entries = []
    with CHAT_LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def append_chat_log(entry: dict) -> None:
    """
    Append one turn, then rewrite the file with only the newest
    MAX_CHAT_LOG_ENTRIES so it cannot grow without bound.
    """
    entries = read_chat_log()
    entries.append(entry)
    entries = entries[-MAX_CHAT_LOG_ENTRIES:]

    with CHAT_LOG_FILE.open("w", encoding="utf-8") as f:
        for item in entries:
            f.write(json.dumps(item) + "\n")


@app.post("/ask")
def ask(request: AskRequest):
    answer, sources = answer_question(request.question, request.history)
    source_list = [{"source": s.source, "doc_type": s.doc_type} for s in sources]

    append_chat_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": request.question,
            "answer": answer,
            "sources": source_list,
        }
    )

    return {
        "answer": answer,
        "sources": source_list,
    }


@app.get("/eval-results")
def eval_results():
    try:
        with open("eval_results.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "No eval results yet"}


@app.get("/chat-log")
def chat_log():
    """Live chat turns, most recent first. Empty list before any question."""
    return list(reversed(read_chat_log()))
