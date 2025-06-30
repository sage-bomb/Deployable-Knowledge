from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional
import json, requests
from utility.embedding_and_storing import db
from config import OLLAMA_URL

router = APIRouter()

@router.post("/chat")
async def chat(message: str = Form(...), inactive: Optional[str] = Form(None)):
    try:
        inactive_sources = set(json.loads(inactive or "[]"))
        embedding = db.embed([message])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=10)
        context_blocks = [
            f"[{i+1}] {doc.strip().replace('\n', ' ')}"
            for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]))
            if meta.get("source") not in inactive_sources
        ]
        prompt = f"""You are a helpful assistant with access to the following context:\n\n{''.join(context_blocks)}\n\nUser: {message}\nAssistant:"""
        response = requests.post(OLLAMA_URL, json={"model": "mistral:7b", "prompt": prompt, "stream": False})
        return JSONResponse(content={"response": response.json().get("response", "[Error: No response]"), "context": context_blocks})
    except Exception as e:
        return JSONResponse(content={"response": f"[Error: {str(e)}]"})

@router.get("/search")
async def search_documents(q: str = Query(...), top_k: int = 5):
    try:
        embedding = db.embed([q])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=top_k)
        enriched_results = [
            {"text": doc, "source": meta.get("source", "unknown"), "score": score}
            for doc, meta, score in zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0],
            )
        ]
        return {"results": enriched_results}
    except Exception as e:
        return {"results": [], "error": str(e)}
