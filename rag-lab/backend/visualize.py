import chromadb
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

DB_NAME = "vector_db"

# Connect to the same vector_db that ingest.py created
client = chromadb.PersistentClient(path=DB_NAME)
collection = client.get_or_create_collection("docs")

# Pull back everything: the vectors themselves, plus their metadata
# (so we can color each point by which folder/doc_type it came from)
result = collection.get(include=["embeddings", "metadatas"])
vectors = result["embeddings"]
doc_types = [m["doc_type"] for m in result["metadatas"]]

# t-SNE squashes each vector (hundreds of numbers) down to just 2 numbers,
# so we can actually plot them on a normal x/y chart.
tsne = TSNE(n_components=2, random_state=42, perplexity=10)
reduced = tsne.fit_transform(vectors)

# Give each doc_type its own color, same idea as the course's chart
colors = {"company": "green", "products": "blue", "employees": "orange", "contracts": "red"}
point_colors = [colors.get(dt, "gray") for dt in doc_types]

plt.figure(figsize=(8, 6))
plt.scatter(reduced[:, 0], reduced[:, 1], c=point_colors)
plt.title("Nexara knowledge base — chunk embeddings (t-SNE)")
plt.savefig("tsne_plot-1.png")
print("Saved chart to tsne_plot-1.png")