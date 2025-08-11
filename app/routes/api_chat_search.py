from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, List
import json
import numpy as np
from sklearn.preprocessing import StandardScaler

from utility.embedding_and_storing import db
from utility import llm_prompt_engine as llm
from utility.session_store import SessionStore
from utility.chat_state import ChatSession
from utility.logger import get_logger
from utility.validation import validate_session_id, clamp_int
from config import MIN_TOP_K, MAX_TOP_K

router = APIRouter()
store = SessionStore()
logger = get_logger(__name__)

def filter_out_chunks(context_blocks, nu=0.4):
    if not context_blocks:
        return []
    scores = np.array([block["score"] for block in context_blocks]).reshape(-1, 1)
    z_scores = StandardScaler().fit_transform(scores)
    return [block for block, z in zip(context_blocks, z_scores) if z < 1]

def search_documents_by_query(query: str, top_k: int = 5, exclude_sources: Optional[set] = None) -> List[Dict]:
    top_k = clamp_int(top_k, MIN_TOP_K, MAX_TOP_K)
    embedding = db.embed([query])[0]
    results = db.collection.query(query_embeddings=[embedding], n_results=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0]

    return [
        {
            "text": doc.strip().replace("\n", " "),
            "source": meta.get("source", "unknown"),
            "score": score,
            "page": meta.get("page", None)
        }
        for doc, meta, score in zip(documents, metadatas, scores)
        if not exclude_sources or meta.get("source", "unknown") not in exclude_sources
    ]

@router.post("/chat")
async def chat(
    message: str = Form(...),
    inactive: Optional[str] = Form(None),
    persona: str = Form(""),
    session_id: str = Form(...),
    stream: bool = Form(False)
):
    session_id = validate_session_id(session_id)
    session = store.load(session_id)
    if session is None:
        logger.info("Creating new chat session for %s", session_id)
        session = ChatSession.new(session_id=session_id, user_id="default")
        store.save(session)

    inactive_sources = set(json.loads(inactive)) if inactive else set()
    raw_blocks = search_documents_by_query(
        message,
        top_k=clamp_int(10 if stream else 5, MIN_TOP_K, MAX_TOP_K),
        exclude_sources=inactive_sources,
    )
    context_blocks = filter_out_chunks(raw_blocks)
    logger.info("Session %s queried with %d context blocks", session_id, len(context_blocks))
    prompt = llm.build_prompt(
        summary=session.summary,
        history=session.history,
        user_message=message,
        context_blocks=context_blocks,
        persona=persona,
    )

    if stream:
        def event_stream():
            assistant_msg = ""
            yield b"<strong>Assistant:</strong><br>"
            for chunk in llm.stream_llm(prompt):
                assistant_msg += chunk
                yield chunk.encode("utf-8")

            html_response = llm.render_response_html(assistant_msg)

            session.add_exchange(
                user=message,
                context_used=context_blocks,
                rag_prompt=prompt,
                assistant=assistant_msg,
                html_response=html_response,
            )
            session.trim_history(20)
            if not session.title:
                session.title = llm.generate_title(
                    f"User: {message}\nAssistant: {assistant_msg}"
                )
            session.summary = llm.update_summary(
                session.summary, message, assistant_msg
            )
            store.save(session)

        return StreamingResponse(event_stream(), media_type="text/html")

    else:
        chatbot_response = llm.ask_llm(prompt)
        html_response = llm.render_response_html(chatbot_response)

        session.add_exchange(
            user=message,
            context_used=context_blocks,
            rag_prompt=prompt,
            assistant=chatbot_response,
            html_response=html_response,
        )
        session.trim_history(20)
        if not session.title:
            session.title = llm.generate_title(
                f"User: {message}\nAssistant: {chatbot_response}"
            )
        session.summary = llm.update_summary(
            session.summary, message, chatbot_response
        )
        store.save(session)

        return JSONResponse(content={
            "response": html_response,
            "context": context_blocks,
            "chat_summary": session.summary,
            "chat_title": session.title,
        })

    # except Exception as e:
    #     return JSONResponse(content={"response": f"[Error: {str(e)}]"})

@router.get("/search")
async def search_documents(
    q: str = Query(...),
    top_k: int = Query(5, ge=MIN_TOP_K, le=MAX_TOP_K),
):
    try:
        results = search_documents_by_query(q, top_k=top_k)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}

@router.post("/chat-stream")
async def legacy_chat_stream(
    message: str = Form(...),
    inactive: Optional[str] = Form(None),
    persona: str = Form(""),
    session_id: str = Form(...)
):
    return await chat(message, inactive, persona, session_id, stream=True)
