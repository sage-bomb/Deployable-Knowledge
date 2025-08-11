from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json, time, shutil
from pathlib import Path

from core.settings import (
    UserSettings,
    load_settings,
    update_settings,
    list_prompt_templates,
    get_prompt_template,
)

router = APIRouter(prefix="/api", tags=["settings"])

@router.get("/settings/{user_id}", response_model=UserSettings)
def get_settings(user_id: str):
    """Fetch persisted settings for ``user_id``."""
    return load_settings(user_id)

@router.patch("/settings/{user_id}", response_model=UserSettings)
def patch_settings(user_id: str, patch: Dict[str, Any]):
    """Apply a partial update to a user's settings."""
    try:
        return update_settings(user_id, patch)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/prompt-templates")
def list_prompts():
    """Return metadata for all available prompt templates."""
    return [p.model_dump() for p in list_prompt_templates()]

@router.get("/prompt-templates/{tid}")
def get_prompt(tid: str):
    """Return a single prompt template by identifier."""
    p = get_prompt_template(tid)
    if not p:
        raise HTTPException(status_code=404, detail="template not found")
    return p.model_dump()

@router.put("/prompt-templates/{tid}")
def put_prompt(tid: str, payload: Dict[str, Any]):
    """Create or replace a prompt template on disk."""
    for f in ["id", "name", "user_format", "system"]:
        if f not in payload:
            raise HTTPException(status_code=400, detail=f"missing {f}")
    if payload["id"] != tid:
        raise HTTPException(status_code=400, detail="id mismatch")
    prompts_dir = Path("prompts")
    prompts_dir.mkdir(exist_ok=True)
    backup_dir = prompts_dir / ".backup"
    backup_dir.mkdir(exist_ok=True)
    target = prompts_dir / f"{tid}.json"
    tmp = prompts_dir / f"{tid}.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if target.exists():
        shutil.copy(target, backup_dir / f"{tid}.{int(time.time())}.json")
    tmp.replace(target)
    return {"status": "ok"}
