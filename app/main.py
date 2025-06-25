import sys
from pathlib import Path
import subprocess

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utility.db_manager import DBManager
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sentence_transformers import SentenceTransformer

from pydantic import BaseModel
from typing import Any, Optional, Dict
from querying.query_handler import QueryHandler

# You may want to move this into a startup hook if using larger models
db = DBManager("chroma_db", "testing_collection")  # path and collection name can be config-driven
query_handler = QueryHandler(db=db, embedder=SentenceTransformer("all-MiniLM-L6-v2"), collection_name="testing_collection")


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()

# Mount static directories
app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

class QueryInput(BaseModel):
    query: str
    k: Optional[int] = 5
    filters: Optional[Dict[str, Dict[str, Any]]] = None

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_class=JSONResponse)
def query_route(data: QueryInput = Body(...)):
    print("Received query:", data.query)  # For logging/debugging
    print("Filters:", data.filters)  # Log filters if any
    results = query_handler.run_query(
        query=data.query,
        k=data.k,
        filters=data.filters
    )
    return {"results": results}

@app.get("/sources")
def get_sources():
    metadatas = query_handler.collection.get(include=["metadatas"])["metadatas"]
    sources = list({meta.get("source") for meta in metadatas if "source" in meta})
    return sources

@app.post("/chat", response_class=JSONResponse)
async def chat(message: str = Form(...)):
    try:
        print(f"Received chat message: {message}")  # For logging/debugAdd commentMore actions

        # Ensure Ollama is installed and 'mistral' is available
        result = subprocess.run(
            ["ollama", "run", "mistral", message],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print("Ollama error:", result.stderr)
            return JSONResponse(status_code=500, content={"reply": f"Ollama error: {result.stderr}"})

        reply = result.stdout.strip()
        print("Ollama replied:", reply)  # Log response
        return {"reply": reply}

    except Exception as e:
        print("Exception in /chat:", e)
        return JSONResponse(status_code=500, content={"reply": f"Error: {e}"})