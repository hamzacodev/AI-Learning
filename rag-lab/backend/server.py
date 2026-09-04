"""
HTTP wrapper around the RAG pipeline, so the Next.js frontend can talk to it.

Run it from THIS directory, because answer.py opens the vector store with the
relative path "vector_db":

    uvicorn server:app --reload --port 8000
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# The pro pipeline: query rewriting, dual search, re-ranking.
# Swap this to answer_basic for the faster, simpler version.
from answer import answer_question

EVAL_RESULTS_FILE = Path(__file__).with_name("eval_results.json")

# The frontend dev server runs on a different port, which makes it a
# different origin, so it has to be allowed explicitly.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app = FastAPI(title="Nexara RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- REQUEST AND RESPONSE SHAPES ---
class AskRequest(BaseModel):
    question: str


class SourceOut(BaseModel):
    source: str
    doc_type: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]


# --- ENDPOINTS ---
@app.get("/health")
def health() -> dict:
    """Cheap check that the server is up, without touching Ollama."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """
    Run one question through the full pipeline.

    Declared with def rather than async def on purpose. The Ollama calls
    block, so FastAPI runs this in its worker threadpool instead of freezing
    the event loop for the 30 to 60 seconds an answer takes.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    answer, chunks = answer_question(question)

    return AskResponse(
        answer=answer,
        sources=[
            SourceOut(source=chunk.source, doc_type=chunk.doc_type)
            for chunk in chunks
        ],
    )


@app.get("/eval-results")
def eval_results() -> dict:
    """
    Serve whatever run_eval.py last wrote.

    A missing file means no evaluation has finished yet. That returns 404,
    which the dashboard shows as an empty state rather than an error.
    """
    if not EVAL_RESULTS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation run recorded yet. Run run_eval.py first.",
        )

    try:
        with EVAL_RESULTS_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail=f"eval_results.json is not valid JSON: {error}",
        ) from error
