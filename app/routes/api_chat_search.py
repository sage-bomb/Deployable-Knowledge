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
            "strike",
            "tables",
            "cuddled-lists"
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

from fastapi.responses import StreamingResponse
import json, requests, markdown2, asyncio

@router.post("/chat-stream")
async def chat_stream(
    message: str = Form(...),
    inactive: Optional[str] = Form(None),
    persona: str = Form("") 
):
    try:
        inactive_sources = set(json.loads(inactive or "[]"))
        embedding = db.embed([message])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=10)

        context_blocks = [
            {
                "text": doc.strip().replace("\n", " "),
                "source": meta.get("source", "unknown"),
                "score": score
            }
            for doc, meta, score in zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0],
            )
            if meta.get("source") not in inactive_sources
        ]

        context_string = "\n\n".join(
            f"[{i+1}] {block['text']}" for i, block in enumerate(context_blocks)
        )

        # === Add user and system persona to prompt ===
        system_persona = "You are a helpful assistant with access to the following context:"
        user_persona = persona.strip()
        persona_block = f"\n\n{user_persona}" if user_persona else ""

        prompt = f"""{system_persona}\n\n{context_string}{persona_block}\n\nUser: {message}\nAssistant:"""

        # === Streaming response ===
        def event_stream():
            response = requests.post(
                OLLAMA_URL,
                json={"model": "mistral:7b", "prompt": prompt, "stream": True},
                stream=True
            )

            yield b"<strong>Assistant:</strong><br>"

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("done"):
                        break
                    if "response" in data:
                        yield data["response"].encode("utf-8")
                except json.JSONDecodeError:
                    continue

        return StreamingResponse(event_stream(), media_type="text/html")

    except Exception as e:
        return JSONResponse(content={"response": f"[Streaming Error: {str(e)}]"})