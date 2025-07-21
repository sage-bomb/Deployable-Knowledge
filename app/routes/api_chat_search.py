from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict
import json, requests, markdown2, threading

from utility.embedding_and_storing import db
from config import OLLAMA_URL

router = APIRouter()

# ==============================
# 🧠 In-memory per-user memory
# ==============================

user_memories: Dict[str, Dict[str, str]] = {}
lock = threading.Lock()

def update_summary(old_summary: str, user_msg: str, assistant_msg: str) -> str:
    prompt = f"""
        [INST] You are a summarizer. Here is the existing summary of a conversation:
        {old_summary}

        Here is the new exchange:
        User: {user_msg}
        Assistant: {assistant_msg}

        Update the summary to include the new exchange. [/INST]
        """.strip()
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "mistral:7b",
            "prompt": prompt,
            "stream": False
        })
        return response.json().get("response", old_summary)
    except Exception:
        return old_summary
    



# ==============================
# POST /chat
# ==============================

@router.post("/chat")
async def chat(
    message: str = Form(...),
    inactive: Optional[str] = Form(None),
    persona: str = Form(""),
    user_id: str = Form(...)
):
    try:
        # Load memory
        with lock:
            memory = user_memories.setdefault(user_id, {"summary": "", "history": []})
            summary = memory["summary"]
            history = memory["history"]

        # Embed + retrieve
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

        # Prompt construction
        history_block = "\n".join(
            f"User: {u}\nAssistant: {a}" for u, a in history[-3:]
        )
        persona_block = f"\n\n{persona.strip()}" if persona.strip() else ""
        prompt = f"""You are a helpful assistant.

            Summary of conversation so far:
            {summary}

            Recent conversation:
            {history_block}

            Context:
            {context_string}
            {persona_block}

            User: {message}
            Assistant:"""

        # Generate response
        response = requests.post(OLLAMA_URL, json={"model": "mistral:7b", "prompt": prompt})
        chatbot_response = response.json().get("response", "[Error: No response]")

        # Format response
        formatted_html = markdown2.markdown(chatbot_response, extras=[
            "fenced-code-blocks", "strike", "tables", "cuddled-lists"
        ])

        # Update memory
        with lock:
            history.append((message, chatbot_response))
            memory["summary"] = update_summary(summary, message, chatbot_response)

        return JSONResponse(content={
            "response": formatted_html,
            "context": context_blocks,
            "chat_summary": memory["summary"]
        })
    except Exception as e:
        return JSONResponse(content={"response": f"[Error: {str(e)}]"})


# ==============================
# GET /search
# ==============================

@router.get("/search")
async def search_documents(q: str = Query(...), top_k: int = 5):
    try:
        embedding = db.embed([q])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=top_k)
        enriched_results = [
            {"text": doc, "source": meta.get("source", "unknown"), "score": score, "page": meta.get("page", None)}
            for doc, meta, score in zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
                results.get("distances", [[]])[0],
            )
        ]
        return {"results": enriched_results}
    except Exception as e:
        return {"results": [], "error": str(e)}


# ==============================
# POST /chat-stream
# ==============================

@router.post("/chat-stream")
async def chat_stream(
    request: Request,
    message: str = Form(...),
    inactive: Optional[str] = Form(None),
    persona: str = Form(""),
    user_id: str = Form(...)
):
    form_data = await request.form()
    message = form_data.get("message", "")
    user_id = form_data.get("user_id", "default")
    persona = form_data.get("persona", "")

    print("📥 Incoming message:", message)
    print("👤 User ID:", user_id)
    print("🎭 Persona:", persona)

    history = user_memories.get(user_id, [])
    print("📜 History:", history)

    try:
        # Load memory
        with lock:
            memory = user_memories.setdefault(user_id, {"summary": "", "history": []})
            summary = memory["summary"]
            history = memory["history"]

        # Embed + retrieve
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

        # Prompt construction
        history_block = "\n".join(
            f"User: {u}\nAssistant: {a}" for u, a in history[-3:]
        )
        persona_block = f"\n\n{persona.strip()}" if persona.strip() else ""
        prompt = f"""You are a helpful assistant.

            Summary of conversation so far:
            {summary}

            Recent conversation:
            {history_block}

            Context:
            {context_string}
            {persona_block}

            User: {message}
            Assistant:"""

        # Streaming response
        def event_stream():
            response = requests.post(
                OLLAMA_URL,
                json={"model": "mistral:7b", "prompt": prompt, "stream": True},
                stream=True
            )

            assistant_msg = ""
            yield b"<strong>Assistant:</strong><br>"

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("done"):
                        break
                    if "response" in data:
                        chunk = data["response"]
                        assistant_msg += chunk
                        yield chunk.encode("utf-8")
                except json.JSONDecodeError:
                    continue

            # After stream ends, update memory
            with lock:
                history.append((message, assistant_msg))
                memory["summary"] = update_summary(summary, message, assistant_msg)

        return StreamingResponse(event_stream(), media_type="text/html")

    except Exception as e:
        return JSONResponse(content={"response": f"[Streaming Error: {str(e)}]"})
    

@router.get("/debug/memory")
async def debug_memory(user_id: Optional[str] = None):
    with lock:
        if user_id:
            memory = user_memories.get(user_id)
            if memory is None:
                return {"error": "User not found"}
            return {user_id: memory}
        else:
            # Return all memory (be cautious if many users)
            return user_memories