from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional
import json, requests
from utility.embedding_and_storing import db
from config import OLLAMA_URL

import markdown2

router = APIRouter()

@router.post("/chat")
async def chat(message: str = Form(...), inactive: Optional[str] = Form(None)):
    try:
        inactive_sources = set(json.loads(inactive or "[]"))
        embedding = db.embed([message])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=10)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        scores = results.get("distances", [[]])[0]

        context_blocks = [
            {
                "text": doc.strip().replace("\n", " "),
                "source": meta.get("source", "unknown"),
                "score": score
            }
            for doc, meta, score in zip(documents, metadatas, scores)
            if meta.get("source") not in inactive_sources
        ]

        context_string = "\n\n".join(
            f"[{i+1}] {block['text']}" for i, block in enumerate(context_blocks)
        )

        prompt = f"""You are a helpful assistant with access to the following context:\n\n{context_string}\n\nUser: {message}\nAssistant:"""
        response = requests.post(OLLAMA_URL, json={"model": "mistral:7b", "prompt": prompt, "stream": False})
        chatbot_response = response.json().get("response", "[Error: No response]")
        formatted_html = markdown2.markdown(chatbot_response, extras=[
            "fenced-code-blocks",
            "code-friendly",
            "strike",
            "header-ids",
            "break-on-newline",
            "tables"
        ])

        print("🚀 Response JSON:", {    "response": formatted_html,    "context": context_blocks})

        return JSONResponse(content={
    "response": formatted_html,
    "context": context_blocks
})
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
