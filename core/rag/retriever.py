from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional, Any
import inspect, re

from config import CHROMA_DB_DIR, COLLECTION_NAME
from .embeddings import load_embedding_model
from .chunking import pagerank_chunk_text
from .chunking import parse_pdf

# --- DB Manager (lightweight wrapper around ChromaDB) ---
import chromadb
from chromadb.config import Settings
import uuid

class DBManager:
    """Minimal wrapper around ChromaDB providing embedding utilities."""

    def __init__(self, persist_dir: str, collection_name: str, model=None):
        self.client = chromadb.PersistentClient(path=str(persist_dir), settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = model or load_embedding_model()

    def clear_collection(self, batch_size: int = 500) -> None:
        """Remove all records from the collection in batches."""

        all_ids = self.collection.get()["ids"]
        total = len(all_ids)
        for i in range(0, total, batch_size):
            batch = all_ids[i:i + batch_size]
            self.collection.delete(ids=batch)

    def embed(self, docs: List[str], max_batch_tokens: int = 5120):
        """Embed ``docs`` using the stored sentence-transformer model."""

        embeddings: List[List[float]] = []
        current_batch: List[str] = []
        current_tokens = 0
        tokenizer = self.model.tokenizer
        for doc in docs:
            tokens = tokenizer.encode(doc, truncation=True, max_length=512)
            truncated_doc = tokenizer.decode(tokens, skip_special_tokens=True)
            num_tokens = len(tokens)
            if num_tokens > max_batch_tokens:
                embeddings.append(self.model.encode(truncated_doc))
                continue
            if current_tokens + num_tokens > max_batch_tokens:
                embeddings.extend(self.model.encode(current_batch))
                current_batch = [truncated_doc]
                current_tokens = num_tokens
            else:
                current_batch.append(truncated_doc)
                current_tokens += num_tokens
        if current_batch:
            embeddings.extend(self.model.encode(current_batch))
        return embeddings

    def build_entry(self, segment_text: str, segment_index: int, source: str, tags: Optional[List[str]] = None, start: Optional[int] = None, end: Optional[int] = None):
        """Build the ID, document and metadata tuple for a segment."""

        segment_uuid = str(uuid.uuid4())
        metadata = {
            "uuid": segment_uuid,
            "source": source,
            "metadata_tags": ", ".join(tags) if tags else "Placeholder",
            "segment_index": segment_index,
            "priority": "medium",
        }
        if start is not None and end is not None:
            metadata["start_char"] = start
            metadata["end_char"] = end
        return segment_uuid, segment_text, metadata

    def add_segments(self, segments: List[str], source: str, tags: Optional[List[str]] = None, positions: Optional[List[tuple]] = None, page: Optional[List[Optional[int]]] = None) -> None:
        """Add many text ``segments`` to the collection."""

        ids: List[str] = []
        docs: List[str] = []
        metas: List[dict] = []
        for i, segment in enumerate(segments):
            start, end = (positions[i] if positions else (-1, -1))
            p = page[i] if page else None
            _id, doc, meta = self.build_entry(segment, i, source, tags, start, end)
            if p is not None:
                meta["page"] = p
            ids.append(_id)
            docs.append(doc)
            metas.append(meta)
        batch_size = 5000
        for i in range(0, len(docs), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = docs[i:i + batch_size]
            batch_metas = metas[i:i + batch_size]
            batch_embeddings = self.embed(batch_docs)
            self.collection.add(ids=batch_ids, documents=batch_docs, metadatas=batch_metas, embeddings=batch_embeddings)

    def delete_by_source(self, source_name: str, batch_size: int = 500) -> None:
        """Remove all segments originating from ``source_name``."""

        all_data = self.collection.get(include=["metadatas"])
        to_delete = [id_ for id_, meta in zip(all_data["ids"], all_data["metadatas"]) if meta.get("source") == source_name]
        for i in range(0, len(to_delete), batch_size):
            batch = to_delete[i:i + batch_size]
            self.collection.delete(ids=batch)

# --- Lazy loader ---
_db: Optional[DBManager] = None

def get_db() -> DBManager:
    """Return a singleton instance of :class:`DBManager`."""

    global _db
    if _db is None:
        model = load_embedding_model()
        _db = DBManager(persist_dir=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, model=model)
    return _db

class LazyDB:
    """Proxy object lazily instantiating :class:`DBManager` on access."""

    def __getattr__(self, name):
        return getattr(get_db(), name)

db = LazyDB()

# --- Chunking helpers from embedding_and_storing ---

def chunk_text(text: str) -> List[Any]:
    """Split ``text`` into ranked chunks for ingestion."""

    return pagerank_chunk_text(text, model=get_db().model, sim_threshold=0.7)

def is_all_caps(text: str, threshold: float = 0.8) -> bool:
    """Heuristic to filter shouty text segments."""

    cleaned = re.sub(r'[\W\d_]+', '', text)
    if not cleaned:
        return False
    upper_count = sum(1 for c in cleaned if c.isupper())
    return (upper_count / len(cleaned)) >= threshold

def has_repeated_substring(text: str, patterns: Optional[List[str]] = None) -> bool:
    """Detect visually noisy substrings such as ellipses or dashes."""

    chars = re.sub(r'\s+', '', text)
    patterns = patterns or [r'\.{3,}', r'-{3,}', r'_{3,}']
    return any(re.search(p, chars) for p in patterns)

def extract_text(file_path: Path) -> List[Dict[str, Any]]:
    """Extract raw text and page numbers from ``file_path``."""

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        parsed = parse_pdf(str(file_path))
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, str):
            return [{"page": 1, "text": parsed}]
        else:
            raise TypeError(f"parse_pdf returned unexpected type: {type(parsed)}")
    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return [{"page": 1, "text": text}]
    raise ValueError(f"Unsupported file type: {file_path.suffix}")

def _db_add_segments_compat(db_obj: DBManager, segments: List[str], source: str, tags: List[str], positions: List[Any], pages: List[Optional[int]], metadata: List[Dict[str, Any]]):
    """Invoke ``db_obj.add_segments`` handling legacy signatures."""

    sig = inspect.signature(db_obj.add_segments)
    params = sig.parameters
    kwargs = dict(segments=segments, source=source, tags=tags)
    if "metadata" in params:
        kwargs["metadata"] = metadata
    else:
        if "positions" in params:
            kwargs["positions"] = positions
        if "page" in params:
            kwargs["page"] = pages
        elif "pages" in params:
            kwargs["pages"] = pages
    return db_obj.add_segments(**kwargs)

def embed_file(file_path: Path, source_name: Optional[str] = None, tags: Optional[List[str]] = None, filter_chunks: bool = True) -> None:
    """Embed a single file into the vector store."""

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    pages_dicts = extract_text(file_path)
    all_chunks: List[Any] = []
    for page in pages_dicts:
        page_num = page.get("page") or 1
        page_text = page.get("text", "")
        chunks_with_meta = chunk_text(page_text)
        for chunk_text_, meta in chunks_with_meta:
            meta["page"] = page_num
            all_chunks.append((chunk_text_, meta))
    if filter_chunks:
        all_chunks = [
            (chunk, meta) for chunk, meta in all_chunks
            if not is_all_caps(chunk) and not has_repeated_substring(chunk)
        ]
    all_chunks = [
        (chunk, meta) for chunk, meta in all_chunks if len(chunk.split()) >= 5
    ]
    segments = [chunk for chunk, _ in all_chunks]
    positions = [meta.get("char_range", (None, None)) for _, meta in all_chunks]
    pages = [meta.get("page") for _, meta in all_chunks]
    metadata = [
        {"char_range": meta.get("char_range"), "page": meta.get("page")}
        for _, meta in all_chunks
    ]
    _db_add_segments_compat(
        db_obj=get_db(),
        segments=segments,
        source=source_name or file_path.name,
        tags=tags or ["embedded"],
        positions=positions,
        pages=pages,
        metadata=metadata,
    )

def embed_directory(data_dir: str, clear_collection: bool = False, default_tags: Optional[List[str]] = None, filter_chunks: bool = False) -> None:
    """Embed all supported files under ``data_dir``."""

    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    if clear_collection:
        get_db().clear_collection()
    for file_path in data_path.iterdir():
        if file_path.suffix.lower() not in {".txt", ".pdf"}:
            continue
        embed_file(file_path=file_path, source_name=file_path.name, tags=default_tags or ["embedded"], filter_chunks=filter_chunks)

def search(query: str, top_k: int = 5, exclude_sources: Optional[set] = None) -> List[Dict]:
    """Perform a vector similarity search over embedded segments."""

    if top_k <= 0:
        return []
    embedding = get_db().embed([query])[0]
    results = get_db().collection.query(query_embeddings=[embedding], n_results=top_k)
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0]
    out = []
    for doc, meta, score in zip(documents, metadatas, scores):
        if exclude_sources and meta.get("source", "unknown") in exclude_sources:
            continue
        out.append({
            "text": doc.strip().replace("\n", " "),
            "source": meta.get("source", "unknown"),
            "score": score,
            "page": meta.get("page", None),
        })
    return out
