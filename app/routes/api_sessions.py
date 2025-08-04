from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from utility.chat_state import ChatSession
from utility.session_store import SessionStore

SESSION_COOKIE_NAME = "chat_session_id"

router = APIRouter()
store = SessionStore()

@router.get("/sessions")
async def list_sessions():
    summaries = []
    for entry in store.list_sessions():
        session_id = entry["id"]
        session = store.load(session_id)
        if session:
            summaries.append(session.to_dict())
    return JSONResponse(content=summaries)

@router.get("/sessions/{session_id}")
async def get_session_data(session_id: str):
    session = store.load(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure each item in history is serialized properly
    history_serialized = []
    for item in getattr(session, "history", []):
        if hasattr(item, "to_dict"):
            history_serialized.append(item.to_dict())
        else:
            history_serialized.append(str(item))  # fallback if no to_dict()

    return JSONResponse(content={
        "id": session_id,
        "created": getattr(session, "created", None),
        "updated": getattr(session, "updated", None),
        "summary": getattr(session, "summary", ""),
        "tokens": getattr(session, "token_count", 0),
        "history": history_serialized,
    })

@router.get("/session")
async def get_or_create_session(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and store.exists(session_id):
        session = store.load(session_id)
    else:
        session = ChatSession.new()
        store.save(session)

    response = JSONResponse({"session_id": session.session_id})
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session.session_id, httponly=False)
    return response
