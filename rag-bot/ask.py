import os
from pathlib import Path

# Redirect the Hugging Face cache into this project folder. On this machine
# ~/.cache is owned by root, so the default cache location isn't writable.
PROJECT_DIR = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(PROJECT_DIR / ".hf_cache"))

import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_DIR = PROJECT_DIR / "chroma_db"
TOP_K = 3
HISTORY_TURNS = 3


def retrieve(collection, model, question: str):
    question_embedding = model.encode([question]).tolist()
    results = collection.query(query_embeddings=question_embedding, n_results=TOP_K)
    chunks = results["documents"][0]
    sources = [meta["source"] for meta in results["metadatas"][0]]
    return list(zip(sources, chunks))


def build_prompt(history: list[tuple[str, str]], retrieved: list[tuple[str, str]], question: str) -> str:
    history_text = "\n\n".join(
        f"Q: {past_question}\nA: {past_answer}" for past_question, past_answer in history[-HISTORY_TURNS:]
    )
    context_text = "\n\n".join(f"[{source}] {chunk}" for source, chunk in retrieved)

    parts = []
    if history_text:
        parts.append(f"Conversation history:\n{history_text}")
    parts.append(f"Context:\n{context_text}")
    parts.append(
        "Answer the question using only the context above. "
        "If the context doesn't contain the answer, say you don't know.\n\n"
        f"Question: {question}"
    )
    return "\n\n".join(parts)


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("Set the GROQ_API_KEY environment variable first.")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection("notes")
    groq_client = Groq(api_key=api_key)

    history: list[tuple[str, str]] = []

    while True:
        question = input("You: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        retrieved = retrieve(collection, model, question)

        print("\nRetrieved chunks:")
        for source, chunk in retrieved:
            print(f"[{source}] \"{chunk}\"")
        print()

        prompt = build_prompt(history, retrieved, question)

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = response.choices[0].message.content

        print(f"Assistant: {answer}\n")

        history.append((question, answer))


if __name__ == "__main__":
    main()
