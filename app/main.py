# === Core Imports ===
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# === FastAPI & Web Imports ===
from fastapi import FastAPI, Request, Form, UploadFile, BackgroundTasks, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import requests

# === Internal Utility Setup ===
BASE_DIR = Path(__file__).resolve().parent.parent
UTIL_DIR = BASE_DIR / "utility"
sys.path.append(str(UTIL_DIR))

# === Local Imports ===
from parsing import parse_pdf
from embedding_and_storing import chunk_text, embed_directory, db

# === FastAPI Setup ===
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

OLLAMA_URL = "http://localhost:11434/api/generate"

# === Utility Functions ===
def get_documents():
    raw = db.collection.get(include=["metadatas"])
    doc_map = {}

    for meta in raw.get("metadatas", []):
        source = meta.get("source", "Untitled")
        if source not in doc_map:
            doc_map[source] = {
                "title": source,
                "count": 1
            }
        else:
            doc_map[source]["count"] += 1

    # Convert map to list of summaries
    return [{"title": title, "id": title, "segments": data["count"]} for title, data in doc_map.items()]

def query_chroma(text: str, top_k: int = 5):
    embedding = db.embed([text])[0]
    results = db.collection.query(query_embeddings=[embedding], n_results=top_k)
    return "\n\n".join(results.get("documents", [[]])[0])

# === Routes ===
@app.get("/", response_class=HTMLResponse)
async def list_documents(request: Request, q: str = ""):
    all_docs = get_documents()
    filtered = [doc for doc in all_docs if q.lower() in doc["title"].lower()] if q else all_docs
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documents": filtered,
        "query": q
    })

@app.post("/upload")
async def upload_pdf(file: UploadFile):
    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        text = parse_pdf(tmp_path)
        chunked = chunk_text(text)
        segments = [chunk for chunk, _ in chunked]
        positions = [meta.get("char_range", (None, None)) for _, meta in chunked]
        db.add_segments(segments, strategy_name="web_ui", source=file.filename, tags=["uploaded"], positions=positions)

        return JSONResponse({"status": "success", "message": f"{file.filename} uploaded and embedded."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

from fastapi import Form
from typing import Optional
import json

@app.post("/chat")
async def chat(message: str = Form(...), inactive: Optional[str] = Form(None)):
    try:
        inactive_sources = set(json.loads(inactive or "[]"))

        query_embedding = db.embed([message])[0]
        results = db.collection.query(query_embeddings=[query_embedding], n_results=10)

        # filter by active state
        docs = []
        context_blocks = []
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            if meta.get("source") not in inactive_sources:
                snippet = doc.strip().replace("\n", " ")
                context_blocks.append(f"[{i+1}] {snippet}")

        context_text = "\n".join(context_blocks)
        prompt = f"""You are a helpful assistant with access to the following context:\n\n{context_text}\n\nUser: {message}\nAssistant:"""

        response = requests.post(OLLAMA_URL, json={
            "model": "mistral:7b",
            "prompt": prompt,
            "stream": False
        })

        result = response.json()
        return JSONResponse(content={
            "response": result.get("response", "[Error: No response]"),
            "context": context_blocks
        })

    except Exception as e:
        return JSONResponse(content={"response": f"[Error: {str(e)}]"})
@app.post("/clear_db")
async def clear_db():
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    pdf_dir = Path("pdfs").resolve()
    txt_dir = Path("documents").resolve()

    if not pdf_dir.exists():
        return {"status": "error", "message": f"Directory not found: {pdf_dir}"}

    for pdf_file in pdf_dir.glob("*.pdf"):
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        try:
            parsed_text = parse_pdf(pdf_file)
            txt_file.write_text(parsed_text, encoding="utf-8")
        except Exception as e:
            print(f"Failed to parse {pdf_file.name}: {e}")

    background_tasks.add_task(
        embed_directory,
        data_dir=str(txt_dir),
        chunking_method="graph",
        clear_collection=False,
        default_tags=["auto_ingested"]
    )

    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}

class SearchResponse(BaseModel):
    results: list[str]

@app.get("/search")
async def search_documents(q: str = Query(...), top_k: int = 5):
    try:
        query_embedding = db.embed([q])[0]
        results = db.collection.query(query_embeddings=[query_embedding], n_results=top_k)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        scores = results.get("distances", [[]])[0]

        enriched_results = [
            {"text": doc, "source": meta.get("source", "unknown"), "score": score}
            for doc, meta, score in zip(docs, metas, scores)
        ]

        return {"results": enriched_results}
    except Exception as e:
        return {"results": [], "error": str(e)}
