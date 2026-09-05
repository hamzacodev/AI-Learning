from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from groq import Groq
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# --- CONFIG ---
DB_NAME = "vector_db_deploy"
EMBED_MODEL = "all-MiniLM-L6-v2"    # same one used during ingestion
CHAT_MODEL = "openai/gpt-oss-20b"  # hosted, served by Groq
RETRIEVAL_K = 5                     # how many chunks to fetch per question

# Loaded once at import, and must match the model ingest_deploy.py used,
# since vectors from two different models are not comparable.
embedder = SentenceTransformer(EMBED_MODEL)


# --- DATA SHAPE ---
# Same idea as the Result class in the course's pro_implementation:
# every retrieved chunk carries its text plus where it came from.
class Result(BaseModel):
    text: str
    source: str
    doc_type: str


# --- CONNECT TO THE VECTOR STORE ---
# Not creating a new one, opening the one ingest_deploy.py already built.
client = chromadb.PersistentClient(path=DB_NAME)
collection = client.get_or_create_collection("docs")


# --- SYSTEM PROMPT TEMPLATE ---
# The developer-written instructions. The {context} placeholder gets
# filled in with retrieved chunks every time a question comes in.
SYSTEM_PROMPT = """You are a helpful assistant for the fictional company Nexara.

For questions about Nexara (the company, its products, employees, contracts),
answer using ONLY the context below.

For questions about the USER (like their name), rely ONLY on what the user
has explicitly stated about themselves earlier in this conversation. NEVER
use names, roles, or facts from the knowledge base context to answer
questions about who the user is, even if a name in the context happens to
match. If the user hasn't stated their own name, say you don't know it.

If information isn't available from the correct source, say you don't know,
don't guess.

Context:
{context}
"""


def fetch_context(question: str) -> list[Result]:
    """
    RETRIEVAL step.
    Turn the question into a vector using the same embedding model
    ingest_deploy.py used, then ask Chroma for the top RETRIEVAL_K closest
    matches. Returns the actual chunks as Result objects.
    """
    # Embed the question
    query_vector = embedder.encode(question).tolist()

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


def answer_question(question: str, history: list = None) -> tuple[str, list[Result]]:
    """
    FULL PIPELINE, same shape as the course's answer_question.
    1. Fetch relevant context
    2. Build the prompt with that context injected
    3. Call the LLM, with any earlier turns sitting between the system
       prompt and the current question
    4. Return the answer text AND the sources it was based on
    """
    # 1. Retrieval. Note this uses the raw question, so a follow-up that only
    # makes sense in context ("what about their pricing") still searches on
    # its own wording.
    chunks = fetch_context(question)

    # 2. Glue chunks into one context block, inject into the system prompt
    context_block = "\n\n".join(c.text for c in chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context_block)

    # 3. Call Groq's chat model with system prompt, prior turns, then question
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})

    response = groq_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0,  # deterministic answers
    )
    answer_text = response.choices[0].message.content

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
