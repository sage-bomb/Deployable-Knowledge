from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.services.user_settings import UserSettings, load_settings, update_settings, list_prompt_templates, get_prompt_template

router = APIRouter(prefix="/api", tags=["settings"])

@router.get("/settings/{user_id}", response_model=UserSettings)
def get_settings(user_id: str):
    return load_settings(user_id)

@router.patch("/settings/{user_id}", response_model=UserSettings)
def patch_settings(user_id: str, patch: Dict[str, Any]):
    try:
        return update_settings(user_id, patch)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/prompt-templates")
def list_prompts():
    return [p.model_dump() for p in list_prompt_templates()]

@router.get("/prompt-templates/{tid}")
def get_prompt(tid: str):
    p = get_prompt_template(tid)
    if not p:
        raise HTTPException(status_code=404, detail="template not found")
    return p.model_dump()

# (OPTIONAL) POST/PUT to add templates can be added later.
