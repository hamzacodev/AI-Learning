import ollama
import chromadb
from pydantic import BaseModel

# --- CONFIG ---
DB_NAME = "vector_db"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.1:8b"
RETRIEVAL_K = 15      # WIDER net: grab more chunks first
FINAL_K = 5           # then narrow to just the best after re-ranking


# --- DATA SHAPES ---
class Result(BaseModel):
    """One retrieved chunk with its source info."""
    text: str
    source: str
    doc_type: str


class RankOrder(BaseModel):
    """
    Locks the LLM's re-ranking response into a strict shape:
    just a list of chunk IDs in relevance order, nothing else.
    Same Pydantic pattern the course used.
    """
    order: list[int]


# --- CONNECT TO VECTOR STORE ---
client = chromadb.PersistentClient(path=DB_NAME)
collection = client.get_or_create_collection("docs")


SYSTEM_PROMPT = """You are a helpful assistant for the fictional company Nexara.
Below is context from Nexara's knowledge base. Read it carefully and answer
the user's question using specific facts from that context.

If the context contains information about multiple items (multiple contracts,
multiple products, multiple employees), summarize ALL of them, don't pick just one.

Only say you don't know if the context genuinely doesn't contain the answer.

Context:
{context}
"""


# ============================================================
# PRO TECHNIQUE #1 — QUERY REWRITING
# ============================================================
def rewrite_query(question: str, history: list = None) -> str:
    """
    Ask the LLM to rewrite the user's question into a clean,
    standalone search query. Especially useful for follow-ups
    like "what about their pricing?" that need conversation
    context to make sense.
    """
    history_text = ""
    if history:
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    prompt = f"""Rewrite the user's question into a short, specific, standalone
search query that will surface relevant content from a knowledge base.
Respond ONLY with the rewritten query, nothing else.

Conversation so far:
{history_text}

Current question: {question}
"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


# ============================================================
# THE UNRANKED SEARCH — used twice (once per query version)
# ============================================================
def fetch_context_unranked(question: str) -> list[Result]:
    """Basic vector search, same as before, just called under a new name."""
    embed_response = ollama.embeddings(model=EMBED_MODEL, prompt=question)
    query_vector = embed_response["embedding"]

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=RETRIEVAL_K,
    )

    chunks = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(
            Result(text=text, source=metadata["source"], doc_type=metadata["doc_type"])
        )
    return chunks


# ============================================================
# PRO TECHNIQUE #2 — DUAL SEARCH + MERGE
# ============================================================
def merge_chunks(chunks1: list[Result], chunks2: list[Result]) -> list[Result]:
    """
    Combine two search result lists, remove duplicates
    (same chunk text = duplicate). Preserves ordering from the first list.
    """
    seen_texts = set()
    merged = []
    for chunk in chunks1 + chunks2:
        if chunk.text not in seen_texts:
            merged.append(chunk)
            seen_texts.add(chunk.text)
    return merged


# ============================================================
# PRO TECHNIQUE #3 — RE-RANKING
# ============================================================
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    """
    Ask the LLM to re-order the chunks by TRUE relevance to the question,
    since raw vector-similarity ordering isn't always right.
    Uses Pydantic response_format to force a strict list-of-ids output.
    """
    # Number each chunk so the LLM can refer to them by ID
    chunks_text = ""
    for i, chunk in enumerate(chunks, start=1):
        chunks_text += f"# CHUNK {i}:\n{chunk.text}\n\n"

    system_prompt = """You are a document re-ranker.
Given a question and a list of numbered chunks, return them re-ordered from
MOST relevant to LEAST relevant.
Reply with ONLY the list of chunk IDs in the new order, no explanation."""

    user_prompt = f"Question: {question}\n\nChunks to re-rank:\n\n{chunks_text}"

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        format=RankOrder.model_json_schema(),   # forces structured output
    )

    ranked = RankOrder.model_validate_json(response["message"]["content"])
    # Rebuild chunks in the new order (subtracting 1 because IDs started at 1)
    return [chunks[i - 1] for i in ranked.order if 1 <= i <= len(chunks)]


# ============================================================
# FULL PIPELINE — puts all three techniques together
# ============================================================
def fetch_context(original_question: str, history: list = None) -> list[Result]:
    """
    Pro retrieval:
    1. Rewrite the question
    2. Search with BOTH original + rewritten
    3. Merge results
    4. Re-rank against the ORIGINAL question (not the rewrite)
    5. Return the top FINAL_K
    """
    rewritten = rewrite_query(original_question, history)

    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten)
    merged = merge_chunks(chunks1, chunks2)

    reranked = rerank(original_question, merged)
    return reranked[:FINAL_K]


def answer_question(question: str, history: list = None) -> tuple[str, list[Result]]:
    """Same shape as before: retrieve, build prompt, call LLM, return answer + sources."""
    chunks = fetch_context(question, history)

    context_block = "\n\n".join(c.text for c in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context_block)

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )
    return response["message"]["content"], chunks


# --- QUICK TEST ---
if __name__ == "__main__":
    # A "spanning" question, one that needs info from multiple chunks
    # Same style of question that gave basic RAG trouble earlier
    test_question = "What contracts do we have with our clients?"
    print(f"Q: {test_question}\n")

    answer, sources = answer_question(test_question)
    print(f"A: {answer}\n")

    print("--- Sources used ---")
    for s in sources:
        print(f"  {s.source} ({s.doc_type})")