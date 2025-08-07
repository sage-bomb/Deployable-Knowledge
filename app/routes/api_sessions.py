from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from utility.chat_state import ChatSession
from utility.session_store import SessionStore
from utility.validation import validate_session_id

SESSION_COOKIE_NAME = "chat_session_id"

router = APIRouter()
store = SessionStore()

@router.get("/sessions")
async def list_sessions():
    """Return lightweight metadata for all stored sessions."""
    summaries = []
    for entry in store.list_sessions():
        session = store.load(entry["id"])
        summaries.append(
            {
                "session_id": entry["id"],
                "title": session.title if session else "",
                "created_at": datetime.fromtimestamp(entry["modified"]).isoformat(),
            }
        )
    return JSONResponse(content=summaries)

@router.get("/sessions/{session_id}")
async def get_session_data(session_id: str):
    """Return the chat history for ``session_id``.

    The frontend expects the history to be a list of ``[user, assistant]``
    pairs, so we convert the stored :class:`ChatExchange` objects to that
    structure here.
    """

    session_id = validate_session_id(session_id)
    session = store.load(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history_pairs = [[ex.user, ex.assistant] for ex in session.history]
    path = store._session_path(session_id)  # access for timestamp metadata
    created_at = (
        datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        if path.exists()
        else None
    )

    return JSONResponse(
        content={
            "session_id": session.session_id,
            "created_at": created_at,
            "summary": session.summary,
            "title": session.title,
            "history": history_pairs,
        }
    )

@router.get("/session")
async def get_or_create_session(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    try:
        session_id = validate_session_id(session_id) if session_id else None
    except ValueError:
        session_id = None
    if session_id and store.exists(session_id):
        session = store.load(session_id)
    else:
        session = ChatSession.new(user_id="default")
        store.save(session)

    response = JSONResponse({"session_id": session.session_id})
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session.session_id, httponly=True)
    return response


@router.post("/session")
async def create_session():
    """Always create and return a new chat session."""

    session = ChatSession.new(user_id="default")
    store.save(session)

    response = JSONResponse({"session_id": session.session_id})
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=session.session_id, httponly=True
    )
    return response
