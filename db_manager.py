
import uuid
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import chromadb

class DBManager:
    """from db_manager import ChromaDBManager
from your_segmentation_module import TopDownSegmenter

db = DBManager("chroma_db", "test_collection")
segmenter = TopDownSegmenter()

segments = segmenter.segment(text)
db.add_segments(segments, strategy_name="top_down", source="contract_001.txt", tags=["legal"])
"""
    def __init__(self, persist_dir: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def clear_collection(self, batch_size=500):
        """Clear the collection in ChromaDB."""
        all_ids = self.collection.get()["ids"]
        total = len(all_ids)
        if not total:
            print("Collection is already empty.")
            return
        for i in range(0, total, batch_size):
            batch = all_ids[i:i + batch_size]
            self.collection.delete(ids=batch)

        print(f"Collection deleted", total, "documents removed.")

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    def build_entry(
        self,
        segment_text: str,
        segment_index: int,
        strategy_name: str,
        source: str,
        tags: Optional[List[str]] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        segment_uuid = str(uuid.uuid4())
        metadata = {
            "uuid": segment_uuid,
            "source": source,
            "parsing_method": strategy_name,
            "metadata_tags": ", ".join(tags) if tags else "Placeholder",
            "segment_index": segment_index,
        }
        if start is not None and end is not None:
            #metadata["char_range"] = [start, end]
            metadata["start_char"] = start
            metadata["end_char"] = end
        return segment_uuid, segment_text, metadata

    def add_segments(
        self,
        segments: List[str],
        strategy_name: str,
        source: str,
        tags: Optional[List[str]] = None,
        positions: Optional[List[tuple]] = None,
    ):
        print("tags:", tags)  # Debugging: print tags
        ids, docs, metas = [], [], []
        for i, segment in enumerate(segments):
            start, end = (positions[i] if positions else (-1, -1))
            _id, doc, meta = self.build_entry(segment, i, strategy_name, source, tags, start, end)
            ids.append(_id)
            docs.append(doc)
            metas.append(meta)

        embeddings = self.embed(docs)
        print(type(metas), metas[:3])  # Debugging: print type and first 3 metadata entries
        self.collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)


