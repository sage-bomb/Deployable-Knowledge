import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from utility.db_manager import DBManager
from utility.parsing import parse_pdf  

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

def extract_text(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        return parse_pdf(str(file_path))
    elif file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

def embed_file(
    file_path: Path,
    chunking_method: str = "graph",
    source_name: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> None:
    """
    Process a single file: parse, chunk, embed, store.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"📄 Embedding file: {file_path.name}")
    text = extract_text(file_path)

    chunks_with_meta = chunk_text(text, method=chunking_method)
    segments = [chunk for chunk, _ in chunks_with_meta]
    positions = [meta.get("char_range", (None, None)) for _, meta in chunks_with_meta]

    db.add_segments(
        segments=segments,
        strategy_name=chunking_method,
        source=source_name or file_path.name,
        tags=tags or ["embedded"],
        positions=positions
    )

    print(f"✅ File embedded: {file_path.name}")


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

    supported_extensions = [".txt", ".pdf"]
    for file_path in data_path.iterdir():
        if file_path.suffix.lower() not in supported_extensions:
            print(f"⚠️ Skipping unsupported file type: {file_path.name}")
            continue

        try:
            embed_file(
                file_path=file_path,
                chunking_method=chunking_method,
                source_name=file_path.name,
                tags=default_tags or ["embedded"]
            )
        except Exception as e:
            print(f"❌ Failed to embed {file_path.name}: {e}")

    print("\n✅ All supported documents embedded and stored.")


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
