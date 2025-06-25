import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from db_manager import DBManager
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from chunking_algs.chunker import (
    chunk_by_sentences,
    chunk_by_semantic_similarity,
    chunk_by_graph_rank,
    chunk_by_paragraphs
)

# === Configuration ===
# Define available chunking methods
CHUNKING_METHOD_OPTIONS = ["sentences", "semantics", "graph", "paragraphs"]

# CLI argument parsing
parser = argparse.ArgumentParser(description="Embed and store text documents with configurable chunking.")
parser.add_argument("--data_dir", type=str, default=os.path.join(current_dir, "documents"), help="Directory with .txt files (newline-preserved from PDFs)")
parser.add_argument("--chunking_method", type=str, default="graph", choices=CHUNKING_METHOD_OPTIONS,
                    help=f"Chunking method to use. Options: {', '.join(CHUNKING_METHOD_OPTIONS)}")
parser.add_argument("--clear_collection", action="store_true", default=True,
                    help="Clear the collection before adding new data (default: True). Use --no-clear_collection to disable.")
parser.add_argument("--no-clear_collection", action="store_false", dest="clear_collection",)
args = parser.parse_args()

# Configuration
DATA_DIR = args.data_dir
CHROMA_PERSIST_DIR = "chroma_db"  # Persistent DB path
CHROMA_COLLECTION_NAME = "testing_collection"
CHUNK_SIZE = 500        # Characters per chunk
CHUNK_OVERLAP = 50      # Overlap between chunks
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNKING_METHOD = args.chunking_method

print(f"Using chunking method: {CHUNKING_METHOD}. Options: {CHUNKING_METHOD_OPTIONS}")
print(f"Reading data from directory: {DATA_DIR}")

# Use DBManager to handle ChromaDB operations
db = DBManager(persist_dir=CHROMA_PERSIST_DIR, collection_name=CHROMA_COLLECTION_NAME)

# Optional: Clear collection if argument is True
if args.clear_collection:
    db.clear_collection()

# Type of chunking method applied
def chunk_text(text: str) -> List[Tuple[str, Dict]]:
    if CHUNKING_METHOD == "sentences":
        return chunk_by_sentences(text, max_chars=500)
    elif CHUNKING_METHOD == "semantics":
        return chunk_by_semantic_similarity(text, model_name=EMBEDDING_MODEL, threshold=0.6)
    elif CHUNKING_METHOD == "graph":
        return chunk_by_graph_rank(text, max_sentences=4)
    elif CHUNKING_METHOD == "paragraphs":
        return chunk_by_paragraphs(text, model_name=EMBEDDING_MODEL, threshold=0.7)
    else:
        raise ValueError(f"Unsupported chunking method: {CHUNKING_METHOD}")

# === Process documents ===
print(f"\nReading from directory: {DATA_DIR}/\n")
for file_path in Path(DATA_DIR).glob("*.txt"):
    print(f"Processing {file_path.name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Perform chunking
    chunked = chunk_text(text)
    segments = [chunk for chunk, _ in chunked]
    positions = [meta.get("char_range") for _, meta in chunked]  # Optional
    metadata_tags = [meta.get("tags", []) for _, meta in chunked]  # Optional, ignored here

    # Add to ChromaDB via DBManager
    print(segments[:3], "...")  # Show first 3 segments for brevity
    db.add_segments(
        segments=segments,
        strategy_name=CHUNKING_METHOD,
        source=file_path.name,
        tags=["testing"],  # Add default/global tags here if needed
        positions=positions
    )

print("\n✅ All documents chunked, embedded, and stored.")