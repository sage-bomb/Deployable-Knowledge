from sentence_transformers import SentenceTransformer
import chromadb
import json
import os

# === Configuration ===
QUERY_FILE = "test_queries.txt"  # One query per line
CHROMA_PERSIST_DIR = "chroma_db"  # Directory where Chroma was saved
CHROMA_COLLECTION_NAME = "testing_collection"  # Must match what's saved
TOP_K = 5  # Number of top results to retrieve
BGE_PREFIX = "Represent this question for retrieval: "  # Format for BGE model
MASTER_RESULTS_JSON = "query_results.json"  # Optional, for saving results in JSON format
EMBEDDING_STRATEGY = "Sentences"

# === Load SentenceTransformer Model ===
print("Loading embedding model...")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")  # Or your specific BGE variant

# === Connect to ChromaDB ===
print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

collection = client.get_collection(CHROMA_COLLECTION_NAME)

# === Load existing results if available ===
if os.path.exists(MASTER_RESULTS_JSON):
    with open(MASTER_RESULTS_JSON, "r", encoding="utf-8") as f:
        results_data = json.load(f)
else:
    results_data = {}

# Ensure model-specific section exists
if EMBEDDING_STRATEGY not in results_data:
    results_data[EMBEDDING_STRATEGY] = {}

# === Read queries ===
with open(QUERY_FILE, "r", encoding="utf-8") as f:
    queries = [line.strip() for line in f if line.strip()]

print(f"\nLoaded {len(queries)} test queries.\n")

# === Run queries ===
for i, query in enumerate(queries, 1):
    formatted_query = f"{BGE_PREFIX}{query}"
    embedding = model.encode([formatted_query])

    if query in results_data[EMBEDDING_STRATEGY]:
        print(f"Skipping already processed query: '{query}'")
        continue

    print(f"Embedding and querying: '{query}'")
    formatted_query = BGE_PREFIX + query
    embedding = model.encode([formatted_query])

    query_result = collection.query(
        query_embeddings=embedding,
        n_results=TOP_K,
        include=["distances", "metadatas", "documents"]
    )

    results_data[EMBEDDING_STRATEGY][query] = {
        "top_results": [
            {
                "document": doc,
                "metadata": meta,
                "distance": float(dist)
            }
            for doc, meta, dist in zip(
                query_result["documents"][0],
                query_result["metadatas"][0],
                query_result["distances"][0]
            )
        ],
        "lowest_distance": float(min(query_result["distances"][0]))
    }

# === Save updated results ===
with open(MASTER_RESULTS_JSON, "w", encoding="utf-8") as f:
    json.dump(results_data, f, indent=2)

    # results = collection.query(
    #     query_embeddings=embedding,
    #     n_results=TOP_K,
    #     include=["metadatas", "distances", "documents"]
    # )

    # print(f"\n=== Query {i}: \"{query}\" ===")
    # with open("query_results.txt", "a", encoding="utf-8") as out_f:
    #     out_f.write(f"\n=== Query {i}: \"{query}\" ===\n")
    #     print(f"\n=== Query {i}: \"{query}\" ===")
    #     for idx, (doc, meta, dist) in enumerate(zip(
    #         results["documents"][0],
    #         results["metadatas"][0],
    #         results["distances"][0]
    #     ), 1):
    #         print(f"Result {idx}:")
    #         print(f"  Text     : {doc}")
    #         print(f"  Metadata : {meta}")
    #         print(f"  Distance : {dist:.4f}")
    #         out_f.write(f"Result {idx}:\n")
    #         out_f.write(f"  Text     : {doc}\n")
    #         out_f.write(f"  Metadata : {meta}\n")
    #         out_f.write(f"  Distance : {dist:.4f}\n")

print("\n✅ Querying complete.")