import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from embed_and_store.db_manager import DBManager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer

# You may want to move this into a startup hook if using larger models
db = DBManager("chroma_db", "testing_collection")  # path and collection name can be config-driven


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()

# Mount static directories
app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_class=JSONResponse)
async def handle_query(q: str = Form(...)):
    # Embed the query
    query_embedding = db.embed([q])[0]

    # Search the vector DB
    results = db.collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    # Structure results for frontend
    formatted = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        formatted.append({
            "source": meta.get("source", "unknown"),
            "preview": doc[:200],  # optional truncation
            "distance": dist,
            "tags": meta.get("metadata_tags", [])
        })

    return {"results": formatted}
