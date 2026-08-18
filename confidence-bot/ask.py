import os 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)


print("Client ready:", client is not None)

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

with open("docs/note1.txt", "r") as f:
 text = f.read()
 embedding = model.encode(text)


print("Text Length:", len(text))
print("Embedding length:", len(embedding))


# def chunk_text(text, chunk_size=20, overlap=5):
#     chunks = []
#     start = 0

#     while start < len(text):
#     end = start + chunk_size
#     chunks.append(text[start:end])
#     start = end - overlap
#     return chunks
def chunk_text(text, chunk_size=20, overlap=5):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

chunks = chunk_text(text)
print("Number of chunks:", len(chunks))
for c in chunks:
    print("-", repr(c))
chunk_embeddings = model.encode(chunks)

print("Number of embeddings:", len(chunk_embeddings))
print("Each embedding length:", len(chunk_embeddings[0]))



# print(chunk_embeddings[0][:5])

# print(chunk_embeddings[2][:5])


import chromadb

chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="confidence_notes")

collection.add(
    documents=chunks,
    embeddings=chunk_embeddings.tolist(),

ids=[f"chunk_{i}" for i in range(len(chunks))])
print("Stored",collection.count(), "chunks in ChromaDB")


question = "What is the capital of France?"
question_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

print("Top matches and their distances:")
for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"- {doc} (distance: {distance})")



    CONFIDENCE_THRESHOLD = 1.5

best_distance = results["distances"][0][0]

if best_distance > CONFIDENCE_THRESHOLD:
    print("I don't know — that doesn't match anything in my notes.")
else:
    print("Best match:", results["documents"][0][0])
    print(f"(confidence distance: {best_distance})")