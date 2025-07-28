
from config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME, LOCAL_MODEL_PATH





import uuid
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class DBManager:
    """from db_manager import ChromaDBManager
from your_segmentation_module import TopDownSegmenter

db = DBManager("chroma_db", "test_collection")
segmenter = TopDownSegmenter()

segments = segmenter.segment(text)
db.add_segments(segments, strategy_name="top_down", source="contract_001.txt", tags=["legal"])
"""
    def __init__(self, persist_dir: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=str(persist_dir), settings=Settings(anonymized_telemetry=False))        
        self.collection = self.client.get_or_create_collection(collection_name)
        model_path = str(LOCAL_MODEL_PATH) if LOCAL_MODEL_PATH.exists() else EMBEDDING_MODEL_NAME
        self.model = SentenceTransformer(model_path) 


    def get_collection(self, name: str):
        return self.client.get_collection(name=name)
    
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

    # def embed(self, texts: List[str]) -> List[List[float]]:
    #     return self.model.encode(texts).tolist()
    
    def embed(self, docs: List[str], max_batch_tokens: int = 5120):
        """
        Embed a list of documents, ensuring each document is truncated to a maximum of 512 tokens.
        This method batches the documents to avoid exceeding the maximum token limit.
        
        Args:
            docs (List[str]): List of documents to embed.
            max_batch_tokens (int): Maximum number of tokens per batch. Default is 5120.

        Returns:
            List[List[float]]: List of embeddings for the documents.
        """
        embeddings = []
        current_batch = []
        current_tokens = 0

        tokenizer = self.model.tokenizer

        for doc in docs:
            # Truncate each doc manually to 512 tokens
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
        strategy_name: str,
        source: str,
        tags: Optional[List[str]] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        """
        Build a segment entry with metadata for storage in the database.

        Args:
            segment_text (str): The text of the segment.
            segment_index (int): The index of the segment.
            strategy_name (str): The name of the segmentation strategy used.
            source (str): The source file or document from which the segment was derived.
            tags (Optional[List[str]]): Optional tags for the segment.
            start (Optional[int]): Optional start character index for the segment.
            end (Optional[int]): Optional end character index for the segment.

        Returns:
            tuple: A tuple containing the segment UUID, segment text, and metadata dictionary.
        """
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
        page: Optional[List[Optional[int]]] = None,
    ):
        """
        Add segments to the database with metadata.

        Args:
            segments (List[str]): List of text segments to add.
            strategy_name (str): Name of the segmentation strategy used.
            source (str): Source file or document from which the segments were derived.
            tags (Optional[List[str]]): Optional tags for the segments.
            positions (Optional[List[tuple]]): Optional list of tuples indicating start and end positions for each segment.
            page (Optional[List[Optional[int]]]): Optional list indicating the page number for each segment.
        
        Returns:
            None
        """
        print("tags:", tags)  # Debugging: print tags
        ids, docs, metas = [], [], []
        for i, segment in enumerate(segments):
            start, end = (positions[i] if positions else (-1, -1))
            p = page[i] if page else None
            _id, doc, meta = self.build_entry(segment, i, strategy_name, source, tags, start, end)
            if p is not None:
                meta["page"] = p
            ids.append(_id)
            docs.append(doc)
            metas.append(meta)

        batch_size=5000    

        for i in range(0, len(docs), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = docs[i:i + batch_size]
            batch_metas = metas[i:i + batch_size]
            batch_embeddings = self.embed(batch_docs)
            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas,
                embeddings=batch_embeddings
            )

    def delete_by_source(self, source_name: str, batch_size=500):
        """
        Delete all entries from the collection that match a given source name.

        Args:
            source_name (str): The source name to match for deletion.
            batch_size (int): Number of entries to delete in each batch. Default is 500.
        
        Returns:
            None
        """
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

