from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import json
import markdown2

from core.models import ChatRequest
from core import pipeline
from core.sessions import SessionStore, ChatSession
from core.prompts import renderer
from api.utils import validate_session_id, clamp_int
from config import MIN_TOP_K, MAX_TOP_K

router = APIRouter()
store = SessionStore()

@router.post("/chat")
async def chat(
    message: str = Form(...),
    session_id: str = Form(...),
    service_id: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    persona: str = Form(""),
    inactive: Optional[str] = Form(None),
    template_id: str = Form("rag_chat"),
    top_k: int = Form(8),
    stream: bool = Query(False),
):
    """Handle a single chat interaction.

    Parameters
    ----------
    message:
        User supplied message content.
    session_id:
        Identifier for the chat session.  A new session is created if the
        provided ID does not exist.
    service_id:
        Identifier of the LLM service to use for this request.
    persona:
        Optional persona string to bias responses.
    inactive:
        JSON encoded list of source IDs to exclude from retrieval.
    template_id:
        Prompt template identifier to use when building the request.
    top_k:
        Number of context chunks to retrieve.
    stream:
        If ``True`` results are returned as a Server‑Sent Events stream.

    Returns
    -------
    JSONResponse or StreamingResponse
        Depending on ``stream`` either a JSON payload containing the chat
        response or an SSE stream of incremental tokens.
    """

    session_id = validate_session_id(session_id)
    session = store.load(session_id) or ChatSession.new(session_id=session_id, user_id="default")
    if inactive:
        session.inactive_sources = json.loads(inactive)
    req = ChatRequest(
        user_id=session.user_id,
        service_id=service_id,
        model_id=model_id,
        message=message,
        persona=persona or session.persona,
        template_id=template_id,
        top_k=clamp_int(top_k, MIN_TOP_K, MAX_TOP_K),
        inactive_sources=session.inactive_sources,
        stream=stream,
    )
    if not stream:
        resp = pipeline.chat_once(req)
        html_response = markdown2.markdown(resp.text)
        session.add_exchange(
            user=message,
            context_used=[s.model_dump() for s in resp.sources],
            rag_prompt="",
            assistant=resp.text,
            html_response=html_response,
        )
        session.trim_history(20)
        if not session.title:
            session.title = renderer.generate_title(f"User: {message}\nAssistant: {resp.text}")
        session.summary = renderer.update_summary(session.summary, message, resp.text)
        store.save(session)
        return JSONResponse(
            {
                "response": html_response,
                "context": [s.model_dump() for s in resp.sources],
                "chat_summary": session.summary,
                "chat_title": session.title,
            }
        )

    async def event_stream():
        assistant = ""
        try:
            for chunk in pipeline.chat_stream(req):
                if chunk.type == "meta":
                    yield f"event: meta\ndata: {chunk.text or '{}'}\n\n"
                elif chunk.type == "delta":
                    assistant += chunk.text or ""
                    yield f"event: delta\ndata: {json.dumps(chunk.text or '')}\n\n"
                elif chunk.type == "done":
                    html_response = markdown2.markdown(assistant)
                    session.add_exchange(
                        user=message,
                        context_used=[s.model_dump() for s in (chunk.sources or [])],
                        rag_prompt="",
                        assistant=assistant,
                        html_response=html_response,
                    )
                    session.trim_history(20)
                    if not session.title:
                        session.title = renderer.generate_title(
                            f"User: {message}\nAssistant: {assistant}"
                        )
                    session.summary = renderer.update_summary(
                        session.summary, message, assistant
                    )
                    store.save(session)
                    payload = {
                        "sources": [s.model_dump() for s in (chunk.sources or [])],
                        "usage": chunk.usage or {},
                    }
                    yield f"event: done\ndata: {json.dumps(payload)}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat-stream")
async def chat_stream(
    message: str = Form(...),
    session_id: str = Form(...),
    service_id: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    persona: str = Form(""),
    inactive: Optional[str] = Form(None),
    template_id: str = Form("rag_chat"),
    top_k: int = Form(8),
):
    """Convenience wrapper that forces streaming mode."""

    return await chat(
        message=message,
        session_id=session_id,
        service_id=service_id,
        model_id=model_id,
        persona=persona,
        inactive=inactive,
        template_id=template_id,
        top_k=top_k,
        stream=True,
    )
