from fastapi import APIRouter, Form, Query, Request, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict
import json, requests, markdown2, threading
from sklearn import svm
from sklearn.preprocessing import StandardScaler
import numpy as np

from utility.embedding_and_storing import db
from config import OLLAMA_URL, OLLAMA_MODEL

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
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        })
        return response.json().get("response", old_summary)
    except Exception:
        return old_summary
    
def filter_out_chunks(context_blocks, nu=0.4):
    if not context_blocks:
        return []

    scores = np.array([block["score"] for block in context_blocks]).reshape(-1,1)
    
    scaler = StandardScaler()
    z_scores = scaler.fit_transform(scores)
    #filtered = scores[z_scores < 1.5]  # or 2.0 if you want to be lenient

    # Filter context_blocks where the corresponding label == 1
    filtered_blocks = [block for block, z in zip(context_blocks, z_scores) if z < 1]
    return filtered_blocks

    



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
    """
    Chat with the assistant.
    This endpoint allows users to send a message to the assistant, which retrieves relevant context from the database,
    generates a response using the Ollama model, and updates the user's memory with the conversation history

    - **message**: The user's message to the assistant.
    - **inactive**: A JSON string of inactive sources to exclude from the context.
    - **persona**: A string representing the user's persona to include in the prompt.
    - **user_id**: A unique identifier for the user to maintain their conversation history.
    - Returns a JSON response with the assistant's response, context blocks, and chat summary.
    """
    try:
        # Load memory
        with lock:
            memory = user_memories.setdefault(user_id, {"summary": "", "history": []})
            summary = memory["summary"]
            history = memory["history"]

        # Embed + retrieve
        inactive_sources = set(json.loads(inactive or "[]"))
        embedding = db.embed([message])[0]
        results = db.collection.query(query_embeddings=[embedding], n_results=5)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        scores = results.get("distances", [[]])[0]

        raw_blocks = [
            {
                "text": doc.strip().replace("\n", " "),
                "source": meta.get("source", "unknown"),
                "score": score
            }
            for doc, meta, score in zip(documents, metadatas, scores)
            if meta.get("source") not in inactive_sources
        ]
        context_blocks = filter_out_chunks(raw_blocks)
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
        response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt})
        chatbot_response = response.json().get("response", "[Error: No response]")

        # Format response
        formatted_html = markdown2.markdown(chatbot_response, extras=[
            "fenced-code-blocks", "strike", "tables", "cuddled-lists"
        ])

        # Update memory
        with lock:
            history.append((message, chatbot_response))
            if len(history) > 20:  # Limit history to last 20 exchanges
                history[:] = history[-20:]
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
    """
    Search for documents in the database using a query string.
    This endpoint retrieves documents that match the query string,
    returning the top K results based on their relevance.

    - **q**: The query string to search for in the documents.
    - **top_k**: The number of top results to return.
    - Returns a JSON response with the search results, including text, source, score, and page number.
    """
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
    """
    Stream chat responses from the assistant.
    This endpoint allows users to send a message to the assistant and receive a streaming response.
    It retrieves relevant context from the database, generates a response using the selected model,
    and updates the user's memory with the conversation history.
    
    - **request**: The FastAPI request object.
    - **message**: The user's message to the assistant.
    - **inactive**: A JSON string of inactive sources to exclude from the context.
    - **persona**: A string representing the user's persona to include in the prompt.
    - **user_id**: A unique identifier for the user to maintain their conversation history.
    - Returns a streaming response with the assistant's response.
    """
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

        raw_blocks = [
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
        context_blocks = filter_out_chunks(raw_blocks)

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
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
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
                if len(history) > 20:
                    history[:] = history[-20:]
                memory["summary"] = update_summary(summary, message, assistant_msg)

        return StreamingResponse(event_stream(), media_type="text/html")

    except Exception as e:
        return JSONResponse(content={"response": f"[Streaming Error: {str(e)}]"})
    

@router.get("/debug/memory")
async def debug_memory(user_id: Optional[str] = None):
    """
    Debug endpoint to view or clear user memory.
    This endpoint allows you to view the memory of a specific user or all users.

    - **user_id**: Optional user ID to filter memory. If not provided, returns all memory.
    - Returns a JSON response with the user's memory or all memory.
    """
    with lock:
        if user_id:
            memory = user_memories.get(user_id)
            if memory is None:
                return {"error": "User not found"}
            return {user_id: memory}
        else:
            # Return all memory (be cautious if many users)
            return user_memories

@router.delete("/debug/memory")
async def delete_memory(user_id: str):
    """
    Delete user memory.
    This endpoint allows you to clear the memory of a specific user.

    - **user_id**: The ID of the user whose memory should be cleared.
    - Returns a JSON response indicating the success or failure of the operation.
    """
    with lock:
        if user_id in user_memories:
            del user_memories[user_id]
            return {"status": "success", "message": f"Memory for user {user_id} cleared."}
        else:
            return {"status": "not_found", "message": f"No memory found for user {user_id}."}

@router.post("/debug/memory")
async def upload_memory(data: dict = Body(...)):
    """
    Upload user memory.
    This endpoint allows you to upload a user's memory, which includes a summary and conversation history.
    
    - **data**: A JSON object containing the user ID, summary, and conversation history.
    - Returns a JSON response indicating the success or failure of the operation.
    """
    user_id = data.get("user_id", "default")
    history = data.get("history", [])
    with lock:
        user_memories[user_id] = {
            "summary": "",
            "history": history
        }
    return {"status": "success", "message": f"Memory for user {user_id} uploaded.", "history_length": len(history)}