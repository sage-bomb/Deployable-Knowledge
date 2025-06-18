from typing import List, Dict, Optional
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer


class QueryHandler:
    def __init__(self, db, embedder:SentenceTransformer, collection_name: Optional[str] = None):
        self.db = db
        self.embedder = embedder
        self.collection: Collection = db.get_collection(name=collection_name) if collection_name else db
    
    def run_query(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict] = None,
        include_metadata: bool = True,
    ) -> List[Dict]:
        """
        Run a semantic search with optional metadata filtering.
        
        :param query: The input query string
        :param k: The number of results (chunks) to return
        :param filters: Metadata filter dictionary
        :param include_metadata: Whether to include metadata in the results
        :return: List of dictionaries with chunks and metadata
        """
        query_embedding = self.embedder.encode([query])[0]

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filters or {},
            include=["documents", "metadatas"] if include_metadata else ["documents"],
        )

        documents = result["documents"][0]
        metadatas = result.get("metadatas", [[]])[0] if include_metadata else [{}] * len(documents)

        return [
            {
                "text": doc,
                "metadata": metadata,
                "tags": metadata.get("tags", []),
                "source": metadata.get("source", None),
                "char_range": metadata.get("char_range", None),
                "start": metadata.get("start", None),
                "end": metadata.get("end", None),
            }
            for doc, metadata in zip(documents, metadatas)
        ]