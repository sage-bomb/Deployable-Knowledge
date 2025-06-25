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
        query_embedding = self.embedder.encode([query])[0]

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filters or {},
            include=["documents", "metadatas", "distances"] if include_metadata else ["documents", "distances"],
        )

        documents = result["documents"][0]
        metadatas = result.get("metadatas", [[]])[0] if include_metadata else [{}] * len(documents)
        distances = result.get("distances", [[]])[0]

        return [
            {
                "preview": doc,
                "metadata": metadata,
                "tags": metadata.get("tags", []),
                "source": metadata.get("source", None),
                "char_range": metadata.get("char_range", None),
                "start": metadata.get("start", None),
                "end": metadata.get("end", None),
                "distance": dist,
            }
            for doc, metadata, dist in zip(documents, metadatas, distances)
        ]
