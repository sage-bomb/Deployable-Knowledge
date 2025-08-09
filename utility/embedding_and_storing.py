from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
import re
import inspect

from utility.db_manager import DBManager
from utility.parsing import parse_pdf
from utility.chunking_algs.graph_pagerank_chunking import pagerank_chunk_text
from utility.model_utils import load_embedding_model

# === Config ===
from config import CHROMA_DB_DIR, COLLECTION_NAME

# === DB / Model Setup ===
embedding_model = load_embedding_model()
db = DBManager(persist_dir=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, model=embedding_model)


# ---------- helpers ----------
def chunk_text(text: str) -> List[Tuple[str, Dict]]:
    """Return [(chunk, meta), ...] using PageRank graph chunker."""
    return pagerank_chunk_text(text, model=embedding_model, sim_threshold=0.7)


def is_all_caps(text: str, threshold: float = 0.8) -> bool:
    """True if text is predominantly uppercase (non-letters ignored)."""
    cleaned = re.sub(r'[\W\d_]+', '', text)
    if not cleaned:
        return False
    upper_count = sum(1 for c in cleaned if c.isupper())
    return (upper_count / len(cleaned)) >= threshold


def has_repeated_substring(text: str, patterns: Optional[List[str]] = None) -> bool:
    """Filter obvious boilerplate/repeat noise like long ellipses/lines."""
    chars = re.sub(r'\s+', '', text)
    patterns = patterns or [r'\.{3,}', r'-{3,}', r'_{3,}']
    return any(re.search(p, chars) for p in patterns)


def extract_text(file_path: Path) -> List[Dict[str, Any]]:
    """
    Always return a list of dicts: [{"page": int, "text": str}, ...]
    Supports .pdf and .txt.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        parsed = parse_pdf(str(file_path))
        if isinstance(parsed, list):
            # assume already [{"page": int, "text": str}, ...]
            return parsed
        elif isinstance(parsed, str):
            return [{"page": 1, "text": parsed}]
        else:
            raise TypeError(f"parse_pdf returned unexpected type: {type(parsed)}")

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return [{"page": 1, "text": text}]

    raise ValueError(f"Unsupported file type: {file_path.suffix}")


def _db_add_segments_compat(
    db_obj: DBManager,
    segments: List[str],
    source: str,
    tags: List[str],
    positions: List[Any],
    pages: List[Optional[int]],
    metadata: List[Dict[str, Any]],
):
    """
    Compatibility layer:
      - If DBManager.add_segments accepts `metadata`, use that.
      - Else pass legacy `positions` and `page` if present.
    """
    sig = inspect.signature(db_obj.add_segments)
    params = sig.parameters
    kwargs = dict(segments=segments, source=source, tags=tags)

    if "metadata" in params:
        kwargs["metadata"] = metadata
    else:
        if "positions" in params:
            kwargs["positions"] = positions
        # Support either `page` or `pages` param names
        if "page" in params:
            kwargs["page"] = pages
        elif "pages" in params:
            kwargs["pages"] = pages

    return db_obj.add_segments(**kwargs)


# ---------- main embedding ----------
def embed_file(
    file_path: Path,
    source_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    filter_chunks: bool = True,
) -> None:
    """
    Parse → chunk → (optionally filter) → embed → store.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"📄 Embedding file: {file_path.name}")

    pages_dicts = extract_text(file_path)  # [{"page": n, "text": "..."}]
    all_chunks_with_meta: List[Tuple[str, Dict[str, Any]]] = []

    for page in pages_dicts:
        page_num = page.get("page") or 1
        page_text = page.get("text", "")
        print(f"Page {page_num} length: {len(page_text)}")

        # Chunk per page
        chunks_with_meta = chunk_text(page_text)

        # Attach page info to each chunk's meta
        for chunk_text_, meta in chunks_with_meta:
            meta["page"] = page_num
            all_chunks_with_meta.append((chunk_text_, meta))

    # Optional filtering
    if filter_chunks:
        all_chunks_with_meta = [
            (chunk, meta) for chunk, meta in all_chunks_with_meta
            if not is_all_caps(chunk) and not has_repeated_substring(chunk)
        ]

    # Drop ultra-short chunks
    all_chunks_with_meta = [
        (chunk, meta) for chunk, meta in all_chunks_with_meta if len(chunk.split()) >= 5
    ]

    # Prepare payloads
    segments = [chunk for chunk, _ in all_chunks_with_meta]
    positions = [meta.get("char_range", (None, None)) for _, meta in all_chunks_with_meta]
    pages = [meta.get("page") for _, meta in all_chunks_with_meta]
    metadata = [
        {"char_range": meta.get("char_range"), "page": meta.get("page")}
        for _, meta in all_chunks_with_meta
    ]

    _db_add_segments_compat(
        db_obj=db,
        segments=segments,
        source=source_name or file_path.name,
        tags=tags or ["embedded"],
        positions=positions,
        pages=pages,
        metadata=metadata,
    )

    print(f"✅ File embedded: {file_path.name}")


def embed_directory(
    data_dir: str,
    clear_collection: bool = False,
    default_tags: Optional[List[str]] = None,
    filter_chunks: bool = False,
) -> None:
    """
    Embed all supported files in a directory.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if clear_collection:
        db.clear_collection()

    print(f"🔍 Embedding from: {data_path.resolve()}")
    print(f"🧹 Clearing collection: {'Yes' if clear_collection else 'No'}")

    supported_extensions = {".txt", ".pdf"}
    for file_path in data_path.iterdir():
        if file_path.suffix.lower() not in supported_extensions:
            print(f"⚠️ Skipping unsupported file type: {file_path.name}")
            continue

        try:
            embed_file(
                file_path=file_path,
                source_name=file_path.name,
                tags=default_tags or ["embedded"],
                filter_chunks=filter_chunks,
            )
        except Exception as e:
            print(f"❌ Failed to embed {file_path.name}: {e}")

    print("\n✅ All supported documents embedded and stored.")


# === CLI Entry ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embed and store text documents (PageRank chunking).")
    parser.add_argument("--data_dir", type=str, default="documents", help="Directory with .txt/.pdf files")
    parser.add_argument("--clear_collection", action="store_true", help="Clear collection before inserting")
    parser.add_argument("--filter_chunks", action="store_true", help="Filter headers/boilerplate during chunking")
    args = parser.parse_args()

    embed_directory(
        data_dir=args.data_dir,
        clear_collection=args.clear_collection,
        default_tags=["testing"],
        filter_chunks=args.filter_chunks,
    )
