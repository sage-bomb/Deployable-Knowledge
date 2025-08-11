from typing import List, Optional
import uuid
import chromadb
from chromadb.config import Settings

from utility.model_utils import load_embedding_model


class DBManager:
    """Wrapper around ChromaDB providing embedding and storage helpers."""

    def __init__(self, persist_dir: str, collection_name: str, model=None):
        self.client = chromadb.PersistentClient(path=str(persist_dir), settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = model or load_embedding_model()

    def get_collection(self, name: str):
        return self.client.get_collection(name=name)

    def clear_collection(self, batch_size: int = 500) -> None:
        """Clear the collection in ChromaDB."""
        all_ids = self.collection.get()["ids"]
        total = len(all_ids)
        if not total:
            print("Collection is already empty.")
            return
        for i in range(0, total, batch_size):
            batch = all_ids[i:i + batch_size]
            self.collection.delete(ids=batch)
        print("Collection deleted", total, "documents removed.")

    def embed(self, docs: List[str], max_batch_tokens: int = 5120):
        """Embed a list of documents, truncating each doc to 512 tokens."""
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

    def build_entry(
        self,
        segment_text: str,
        segment_index: int,
        source: str,
        tags: Optional[List[str]] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        """Build a segment entry with metadata for storage in the database."""
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

    def add_segments(
        self,
        segments: List[str],
        source: str,
        tags: Optional[List[str]] = None,
        positions: Optional[List[tuple]] = None,
        page: Optional[List[Optional[int]]] = None,
    ) -> None:
        """Add segments to the database with metadata."""
        print("tags:", tags)
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
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeddings,
            )

    def delete_by_source(self, source_name: str, batch_size: int = 500) -> None:
        """Delete all entries from the collection that match a given source name."""
        all_data = self.collection.get(include=["metadatas"])
        to_delete = [
            id_ for id_, meta in zip(all_data["ids"], all_data["metadatas"])
            if meta.get("source") == source_name
        ]
        total = len(to_delete)
        if not total:
            print(f"No documents found for source: {source_name}")
            return
        for i in range(0, total, batch_size):
            batch = to_delete[i:i + batch_size]
            self.collection.delete(ids=batch)
        print(f"🗑️ Deleted {total} segments for source: {source_name}")
