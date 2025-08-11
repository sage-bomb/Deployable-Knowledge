from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse 

from fastapi.templating import Jinja2Templates
from pathlib import Path
from core.rag.retriever import db
from core.sessions import ChatSession, SessionStore
from api.utils import validate_session_id

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

SESSION_COOKIE_NAME = "chat_session_id"
store = SessionStore()

def get_documents():
    raw = db.collection.get(include=["metadatas"])
    doc_map = {}
    for meta in raw.get("metadatas", []):
        source = meta.get("source", "Untitled")
        if source not in doc_map:
            doc_map[source] = {"title": source, "count": 1}
        else:
            doc_map[source]["count"] += 1
    return [{"title": k, "id": k, "segments": v["count"]} for k, v in doc_map.items()]

@router.get("/documents")
async def list_documents_json():
    return get_documents()

@router.get("/", response_class=HTMLResponse)
async def front_door(request: Request, q: str = ""):
    """
    Splash if no USER session; main index if user session is valid.
    """
    # 1) Is there a valid *user* session cookie? (no CSRF check on GET)
    manager = request.app.state.session_manager
    try:
        _ = manager.fetch_valid_session(request, require_csrf=False)
        has_user_session = True
    except Exception:
        has_user_session = False

    # 2) If no user session -> show splash page (no cookies issued here)
    if not has_user_session:
        return templates.TemplateResponse("splash.html", {"request": request})

    # 3) Otherwise proceed with your existing *chat* session logic
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
        session_id = session.session_id

    all_docs = get_documents()
    filtered = [doc for doc in all_docs if q.lower() in doc["title"].lower()] if q else all_docs

    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "documents": filtered,
            "query": q,
            "session_id": session_id,
        },
    )
    # keep your existing chat-session cookie
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session.session_id, httponly=True)
    return response


@router.get("/begin")
async def begin(request: Request):
    """
    Issue the USER session (session_id + csrf_token) then bounce back to "/".
    """
    resp = RedirectResponse(url="/", status_code=303)
    manager = request.app.state.session_manager
    manager.issue(resp, request, user_id="local-user")  # swap to SSO later
    return resp

@router.get("/logout")
async def logout(request: Request):
    """
    Kill the USER session (server-side + cookies) and the per-chat cookie,
    then return to splash (/).
    """
    resp = RedirectResponse("/", status_code=303)
    manager = request.app.state.session_manager

    # Try to delete the server-side user session if present
    sid = request.cookies.get("__Host-session_id") or request.cookies.get("session_id")
    if sid:
        try:
            manager.store.delete(sid)
        except Exception:
            pass

    # Nuke cookies (both possible session cookie names, plus CSRF + chat-session)
    resp.delete_cookie("__Host-session_id", path="/")
    resp.delete_cookie("session_id", path="/")
    resp.delete_cookie("csrf_token", path="/")
    # your per-chat cookie:
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")

    return resp