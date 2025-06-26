import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

import httpx

# === Setup Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
UTIL_DIR = BASE_DIR / "utility"
sys.path.append(str(UTIL_DIR))

# === Imports from Utilities ===
from parsing import parse_pdf
from embedding_and_storing import chunk_text, db


# === FastAPI Setup ===
app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

OLLAMA_URL = "http://localhost:11434/api/generate"


# === Utilities ===
def get_documents():
    raw = db.collection.get(include=["metadatas"])
    seen = set()
    docs = []
    for meta in raw.get("metadatas", []):
        uid = meta.get("uuid")
        if uid and uid not in seen:
            docs.append({
                "title": meta.get("source", "Untitled"),
                "id": uid
            })
            seen.add(uid)
    return docs


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

        # Parse, chunk, and embed
        text = parse_pdf(tmp_path)
        chunked = chunk_text(text)
        segments = [chunk for chunk, _ in chunked]
        positions = [meta.get("char_range", (None, None)) for _, meta in chunked]
        db.add_segments(segments, strategy_name="web_ui", source=file.filename, tags=["uploaded"], positions=positions)

        return JSONResponse({"status": "success", "message": f"{file.filename} uploaded and embedded."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})


@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        # Step 1: Embed user message
        query_embedding = db.embed([message])[0]

        # Step 2: Query top 2 matching chunks
        results = db.collection.query(query_embeddings=[query_embedding], n_results=2)

        docs = results.get("documents", [[]])[0]
        sources = results.get("metadatas", [[]])[0]

        # Step 3: Prepend context to prompt
        context_blocks = [f"• {doc.strip()}" for doc in docs]
        context_text = "\n".join(context_blocks)

        prompt = f"""You are a helpful assistant with access to the following context:

{context_text}

User: {message}
Assistant:"""

        # Step 4: Send to LLM (Ollama)
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:11434/api/generate", json={
                "model": "mistral:7b",
                "prompt": prompt,
                "stream": False
            })
            result = response.json()
            return JSONResponse(content={"response": result.get("response", "[Error: No response]")})
    except Exception as e:
        return JSONResponse(content={"response": f"[Error: {str(e)}]"})


@app.post("/clear_db")
async def clear_db():
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

from fastapi import BackgroundTasks
from embedding_and_storing import embed_directory

from utility.parsing import parse_pdf
from pathlib import Path

@app.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    pdf_dir = Path("pdfs").resolve()
    txt_dir = Path("documents").resolve()
    
    print(f"🔍 Looking for PDFs in: {pdf_dir}")
    print(f"📁 Saving .txt to: {txt_dir}")

    if not pdf_dir.exists():
        print("❌ PDF directory does not exist.")
        return {"status": "error", "message": f"Directory not found: {pdf_dir}"}

    files = list(pdf_dir.glob("*.pdf"))
    print(f"📄 Found {len(files)} PDFs")

    for pdf_file in files:
        txt_file = txt_dir / (pdf_file.stem + ".txt")
        try:
            print(f"📝 Parsing {pdf_file.name} → {txt_file.name}")
            parsed_text = parse_pdf(pdf_file)
            txt_file.write_text(parsed_text, encoding="utf-8")
        except Exception as e:
            print(f"⚠️ Failed to parse {pdf_file.name}: {e}")

    background_tasks.add_task(
        embed_directory,
        data_dir=str(txt_dir),
        chunking_method="graph",
        clear_collection=False,
        default_tags=["auto_ingested"]
    )

    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}

from fastapi import Query
from pydantic import BaseModel

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

        enriched_results = []
        for doc, meta, score in zip(docs, metas, scores):
            enriched_results.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": score
            })

        return {"results": enriched_results}
    except Exception as e:
        return {"results": [], "error": str(e)}