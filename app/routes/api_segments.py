from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from utility.embedding_and_storing import db

router = APIRouter()

@router.get("/segments")
async def list_segments():
    data = db.collection.get(include=["documents", "metadatas", "ids"])
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
    try:
        db.collection.delete(ids=[seg_id])
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
