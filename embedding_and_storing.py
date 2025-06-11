import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from uuid import uuid4

# === Configuration ===
DATA_DIR = "documents"  # Directory with .txt files (newline-preserved from PDFs)
CHROMA_PERSIST_DIR = "chroma_db"  # Persistent DB path
CHROMA_COLLECTION_NAME = "testing_collection"
CHUNK_SIZE = 500        # Characters per chunk
CHUNK_OVERLAP = 50      # Overlap between chunks
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
BGE_PREFIX = "Represent this passage for retrieval: "  # Required for BGE model

# === Initialize model and client ===
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

print("Connecting to persistent ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# === Failsafe: (Re)create collection ===
if CHROMA_COLLECTION_NAME in [c.name for c in client.list_collections()]:
    print(f"Collection '{CHROMA_COLLECTION_NAME}' already exists. Deleting for fresh ingestion...")
    client.delete_collection(CHROMA_COLLECTION_NAME)

collection = client.create_collection(CHROMA_COLLECTION_NAME)
print(f"Collection '{CHROMA_COLLECTION_NAME}' created.\n")

# === Static chunking function ===
def chunk_text_with_lines(text, chunk_size, overlap):
    """Chunks text while tracking line numbers for metadata."""
    lines = text.splitlines()
    full_text = "\n".join(lines)
    chunks, line_info = [], []

    start_char = 0
    while start_char < len(full_text):
        end_char = min(start_char + chunk_size, len(full_text))
        chunk = full_text[start_char:end_char]
        chunk_start_line = full_text[:start_char].count('\n')
        chunks.append(chunk)
        line_info.append(chunk_start_line)
        start_char += chunk_size - overlap

    return chunks, line_info

# === Process all .txt documents ===
print(f"Reading from directory: {DATA_DIR}/\n")
for file_path in Path(DATA_DIR).glob("*.txt"):
    print(f"Processing {file_path.name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks, line_info = chunk_text_with_lines(text, CHUNK_SIZE, CHUNK_OVERLAP)
    formatted_chunks = [BGE_PREFIX + chunk for chunk in chunks]
    embeddings = model.encode(formatted_chunks)

    ids = [str(uuid4()) for _ in chunks]
    metadatas = [
        {
            "source": file_path.name,
            "chunk_idx": i,
            "start_line": line_info[i]
        }
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

print("\n✅ All documents processed and stored in ChromaDB.")
