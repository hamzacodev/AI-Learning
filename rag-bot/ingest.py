import os
from pathlib import Path

# Redirect the Hugging Face cache into this project folder. On this machine
# ~/.cache is owned by root, so the default cache location isn't writable.
PROJECT_DIR = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(PROJECT_DIR / ".hf_cache"))

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = PROJECT_DIR / "docs"
CHROMA_DIR = PROJECT_DIR / "chroma_db"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def main() -> None:
    txt_files = sorted(DOCS_DIR.glob("*.txt"))
    if not txt_files:
        raise SystemExit(f"No .txt files found in {DOCS_DIR}")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Reset the collection each run so re-running this script doesn't hit
    # duplicate-ID errors from a previous ingest.
    try:
        client.delete_collection("notes")
    except Exception:
        pass
    collection = client.create_collection("notes")

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for file_path in txt_files:
        text = file_path.read_text(encoding="utf-8").strip()
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{file_path.stem}_{i}")
            all_metadatas.append({"source": file_path.name, "chunk_index": i})

    embeddings = model.encode(all_chunks).tolist()

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )

    print(f"Created and stored {len(all_chunks)} chunks in ChromaDB collection 'notes'.")


if __name__ == "__main__":
    main()
