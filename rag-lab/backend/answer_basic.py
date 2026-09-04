import ollama
import chromadb
from pydantic import BaseModel

# --- CONFIG ---
DB_NAME = "vector_db"
EMBED_MODEL = "nomic-embed-text"   # same one used during ingestion
CHAT_MODEL = "llama3.1:8b"          # our local "gpt-4.1-nano" equivalent
RETRIEVAL_K = 5                     # how many chunks to fetch per question


# --- DATA SHAPE ---
# Same idea as the Result class in the course's pro_implementation:
# every retrieved chunk carries its text plus where it came from.
class Result(BaseModel):
    text: str
    source: str
    doc_type: str


# --- CONNECT TO THE VECTOR STORE ---
# Not creating a new one, opening the one ingest.py already built.
client = chromadb.PersistentClient(path=DB_NAME)
collection = client.get_or_create_collection("docs")


# --- SYSTEM PROMPT TEMPLATE ---
# The developer-written instructions. The {context} placeholder gets
# filled in with retrieved chunks every time a question comes in.
SYSTEM_PROMPT = """You are a helpful assistant for the fictional company Nexara.
Answer the user's question using ONLY the context provided below.
If the answer isn't in the context, say you don't know, don't make things up.

Context:
{context}
"""


def fetch_context(question: str) -> list[Result]:
    """
    RETRIEVAL step.
    Turn the question into a vector using the same embedding model
    ingest.py used, then ask Chroma for the top RETRIEVAL_K closest matches.
    Returns the actual chunks as Result objects.
    """
    # Embed the question
    embed_response = ollama.embeddings(model=EMBED_MODEL, prompt=question)
    query_vector = embed_response["embedding"]

    # Search Chroma for the closest matches
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=RETRIEVAL_K,
    )

    # Package the raw Chroma output into our clean Result objects
    chunks = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(
            Result(text=text, source=metadata["source"], doc_type=metadata["doc_type"])
        )
    return chunks


def answer_question(question: str) -> tuple[str, list[Result]]:
    """
    FULL PIPELINE, same shape as the course's answer_question.
    1. Fetch relevant context
    2. Build the prompt with that context injected
    3. Call the LLM
    4. Return the answer text AND the sources it was based on
    """
    # 1. Retrieval
    chunks = fetch_context(question)

    # 2. Glue chunks into one context block, inject into the system prompt
    context_block = "\n\n".join(c.text for c in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context_block)

    # 3. Call Ollama's chat model with system prompt + user question
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )
    answer_text = response["message"]["content"]

    # 4. Return both the answer AND the sources (for showing them in the UI later)
    return answer_text, chunks


# --- QUICK TEST ---
# Same "if __name__" pattern from the course.
# Run this file directly and it'll ask one hardcoded test question.
if __name__ == "__main__":
    test_question = "What's the contract value with our clients?"
    print(f"Q: {test_question}\n")

    answer, sources = answer_question(test_question)
    print(f"A: {answer}\n")

    print("--- Sources used ---")
    for s in sources:
        print(f"  {s.source} ({s.doc_type})")