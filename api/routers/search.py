from fastapi import APIRouter, Query
from typing import Optional
import json

from core.rag import retriever
from api.utils import clamp_int
from config import MIN_TOP_K, MAX_TOP_K

router = APIRouter()

@router.get("/search")
def search(q: str = Query(...), top_k: int = Query(5, ge=MIN_TOP_K, le=MAX_TOP_K), inactive: Optional[str] = Query(None)):
    """Perform a similarity search against the document store."""

    exclude = set(json.loads(inactive)) if inactive else None
    results = retriever.search(q, top_k=clamp_int(top_k, MIN_TOP_K, MAX_TOP_K), exclude_sources=exclude)
    return {"results": results}
