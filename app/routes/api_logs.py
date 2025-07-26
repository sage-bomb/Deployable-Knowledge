from fastapi import APIRouter, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from typing import Optional

from utility.log_manager import LogManager

router = APIRouter()
log_manager = LogManager()

@router.post("/logs/start")
async def start_session(user_id: str = Form(...)):
    session_id = log_manager.start_session(user_id)
    return {"session_id": session_id}

@router.get("/logs")
async def list_logs(user_id: str = Query(...)):
    sessions = log_manager.list_sessions(user_id)
    return {"sessions": sessions}

@router.get("/logs/{session_id}")
async def get_log(session_id: str):
    data = log_manager.load_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data
