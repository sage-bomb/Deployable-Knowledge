from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from utility.embedding_and_storing import db

router = APIRouter()

def get_documents():
    raw = db.collection.get(include=["metadatas"])
    doc_map = {}
    for meta in raw.get("metadatas", []):
        source = meta.get("source", "Untitled")
        if source not in doc_map:
            doc_map[source] = {"title": source, "count": 1}
        else:
            doc_map[source]["count"] += 1
    return [{"title": k, "id": k, "segments": v["count"]} for k, v in doc_map.items()]

@router.get("/", response_class=HTMLResponse)
async def list_documents(request: Request, q: str = ""):
    from app.main import templates
    all_docs = get_documents()
    filtered = [doc for doc in all_docs if q.lower() in doc["title"].lower()] if q else all_docs
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documents": filtered,
        "query": q
    })
