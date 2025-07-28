from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from utility.embedding_and_storing import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

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

@router.get("/documents")
async def list_documents_json():
    """
    List all documents in the database as JSON.
    This endpoint retrieves all documents stored in the database and returns them in JSON format.

    - Returns a JSON response with a list of documents, each containing title, id, and segment count.
    """
    return get_documents()

@router.get("/", response_class=HTMLResponse)
async def list_documents(request: Request, q: str = ""):
    """
    Render the main page with a list of documents.
    This endpoint retrieves all documents and renders them in an HTML template.
    
    - **request**: The FastAPI request object.
    - **q**: Optional query string to filter documents by title.
    - Returns an HTML response with the rendered template containing the list of documents.
    """
    all_docs = get_documents()
    filtered = [doc for doc in all_docs if q.lower() in doc["title"].lower()] if q else all_docs
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documents": filtered,
        "query": q
    })
