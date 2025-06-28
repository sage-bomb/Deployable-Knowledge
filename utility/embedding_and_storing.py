import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from utility.db_manager import DBManager

# Import chunkers
from utility.chunking_algs.chunker import (
    chunk_by_sentences,
    chunk_by_semantic_similarity,
    chunk_by_graph_rank,
    chunk_by_paragraphs
)

# === Config ===
DEFAULT_CHROMA_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "testing_collection"
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNKING_METHOD_OPTIONS = ["sentences", "semantics", "graph", "paragraphs"]

# === DB Setup ===
db = DBManager(persist_dir=DEFAULT_CHROMA_DIR, collection_name=DEFAULT_COLLECTION_NAME)


def chunk_text(text: str, method: str = "graph") -> List[Tuple[str, Dict]]:
    if method == "sentences":
        return chunk_by_sentences(text, max_chars=500)
    elif method == "semantics":
        return chunk_by_semantic_similarity(text, model_name=DEFAULT_EMBEDDING_MODEL, threshold=0.6)
    elif method == "graph":
        return chunk_by_graph_rank(text, max_sentences=4)
    elif method == "paragraphs":
        return chunk_by_paragraphs(text, model_name=DEFAULT_EMBEDDING_MODEL, threshold=0.7)
    else:
        raise ValueError(f"Unsupported chunking method: {method}")


def embed_directory(
    data_dir: str,
    chunking_method: str = "graph",
    clear_collection: bool = False,
    default_tags: Optional[List[str]] = None,
):
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if clear_collection:
        db.clear_collection()

    print(f"🔍 Embedding from: {data_path.resolve()}")
    print(f"📚 Using method: {chunking_method}")
    print(f"🧹 Clearing collection: {'Yes' if clear_collection else 'No'}")

    for file_path in data_path.glob("*.txt"):
        print(f"→ Processing {file_path.name}...")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunked = chunk_text(text, method=chunking_method)
        segments = [chunk for chunk, _ in chunked]
        positions = [meta.get("char_range", (None, None)) for _, meta in chunked]

        db.add_segments(
            segments=segments,
            strategy_name=chunking_method,
            source=file_path.name,
            tags=default_tags or ["embedded"],
            positions=positions
        )

    print("\n✅ All documents embedded and stored.")


# === CLI Entry ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embed and store text documents with configurable chunking.")
    parser.add_argument("--data_dir", type=str, default="documents", help="Directory with .txt files")
    parser.add_argument("--chunking_method", type=str, default="graph", choices=CHUNKING_METHOD_OPTIONS)
    parser.add_argument("--clear_collection", action="store_true", help="Clear collection before inserting")
    args = parser.parse_args()

    embed_directory(
        data_dir=args.data_dir,
        chunking_method=args.chunking_method,
        clear_collection=args.clear_collection,
        default_tags=["testing"]
    )
