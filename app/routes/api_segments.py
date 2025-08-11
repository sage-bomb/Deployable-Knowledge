from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from core.rag.retriever import db

router = APIRouter()

@router.get("/segments")
async def list_segments():
    """Return brief information about all stored text segments."""
    data = db.collection.get(include=["documents", "metadatas"])
    segments = []
    docs = data.get("documents", [])
    metas = data.get("metadatas", [])
    ids = data.get("ids", [])
    for doc, meta, _id in zip(docs, metas, ids):
        segments.append({
            "id": _id,
            "source": meta.get("source", "unknown"),
            "preview": doc[:80],
            "priority": meta.get("priority", "medium")
        })
    return JSONResponse(content=segments)

@router.delete("/segments/{seg_id}")
async def delete_segment(seg_id: str):
    """Remove a single segment by identifier."""
    try:
        db.collection.delete(ids=[seg_id])
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments/{seg_id}")
async def get_segment(seg_id: str):
    """Fetch the full text and metadata for ``seg_id``."""
    data = db.collection.get(ids=[seg_id], include=["documents", "metadatas"])
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    if not docs:
        raise HTTPException(status_code=404, detail="segment not found")
    doc = docs[0]
    meta = metas[0] if metas else {}
    return {"id": seg_id, "text": doc, **meta}
