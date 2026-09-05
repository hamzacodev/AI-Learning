import os
import glob
import chromadb
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


KNOWLEDGE_BASE = "nexara-docs"
DB_NAME = "vector_db_deploy"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Loaded once at import, since loading the weights is the slow part.
embedder = SentenceTransformer(EMBED_MODEL)


class Chunk(BaseModel):
    text: str
    source: str
    doc_type: str


def fetch_documents():
    """Read every .md file, tag each with its folder name."""
    documents = []
    for folder in glob.glob(f"{KNOWLEDGE_BASE}/*"):
        doc_type = os.path.basename(folder)
        for filepath in glob.glob(f"{folder}/*.md"):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append({"text": text, "source": filepath, "doc_type": doc_type})
    return documents


def chunk_text(text, chunk_size=500, overlap=100):
    """Split on paragraph breaks first, keep pieces under chunk_size, add overlap."""
    paragraphs = text.split("\n\n")
    chunks, current = [], ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            current = para + "\n\n"

    if current.strip():
        chunks.append(current.strip())

    overlapped = []
    for i, chunk in enumerate(chunks):
        if i > 0:
            tail = chunks[i - 1][-overlap:]
            chunk = tail + " " + chunk
        overlapped.append(chunk)

    return overlapped


def create_chunks(documents):
    """Turn raw documents into a flat list of Chunk objects."""
    all_chunks = []
    for doc in documents:
        pieces = chunk_text(doc["text"])
        for piece in pieces:
            all_chunks.append(
                Chunk(text=piece, source=doc["source"], doc_type=doc["doc_type"])
            )
    return all_chunks


def create_embeddings(chunks):
    """Embed each chunk with sentence-transformers, store chunk + vector in Chroma."""
    client = chromadb.PersistentClient(path=DB_NAME)
    collection = client.get_or_create_collection("docs")

    for i, chunk in enumerate(chunks):
        vector = embedder.encode(chunk.text).tolist()
        collection.add(
            ids=[str(i)],
            embeddings=[vector],
            documents=[chunk.text],
            metadatas=[{"source": chunk.source, "doc_type": chunk.doc_type}],
        )

    print(f"Stored {len(chunks)} chunks in {DB_NAME}")


if __name__ == "__main__":
    docs = fetch_documents()
    print(f"Loaded {len(docs)} documents")

    chunks = create_chunks(docs)
    print(f"Created {len(chunks)} chunks")

    create_embeddings(chunks)
