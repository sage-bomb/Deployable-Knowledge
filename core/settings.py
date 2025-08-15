from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
import json
from pydantic import BaseModel, Field, ConfigDict

from .prompts import loader as prompt_loader

USERS_DIR = Path("users")
USERS_DIR.mkdir(parents=True, exist_ok=True)


class OllamaSettings(BaseModel):
    """Configuration for an Ollama model endpoint."""

    host: str = "http://localhost:11434"
    model: str = ""


class OpenAISettings(BaseModel):
    """Configuration for an OpenAI ChatGPT model."""

    model: str = ""
    api_key: str = ""


class UserSettings(BaseModel):
    user_id: str
    llm_provider: Literal["ollama", "openai"] = "ollama"
    llm_model: str = ""
    prompt_template_id: Optional[str] = None
    temperature: float = 0.2
    top_p: float = 0.95
    max_tokens: int = 512
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)

def _user_path(user_id: str) -> Path:
    """Location of the settings file for ``user_id``."""

    return USERS_DIR / f"{user_id}.json"

def load_settings(user_id: str) -> UserSettings:
    """Load settings for ``user_id`` creating defaults if necessary."""

    p = _user_path(user_id)
    if not p.exists():
        s = UserSettings(user_id=user_id)
        save_settings(s)
        return s
    data = json.loads(p.read_text(encoding="utf-8"))
    return UserSettings(**data)

def save_settings(s: UserSettings) -> None:
    """Persist ``s`` to its JSON file."""

    p = _user_path(s.user_id)
    p.write_text(s.model_dump_json(indent=2), encoding="utf-8")

def update_settings(user_id: str, patch: Dict[str, Any]) -> UserSettings:
    """Apply ``patch`` to a user's settings and persist the result."""

    s = load_settings(user_id)
    s = s.model_copy(update=patch)
    save_settings(s)
    return s

# Prompt template helpers
PROMPTS_DIR = Path("prompts")
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: Optional[str] = None
    system: Optional[str] = None
    content: Optional[str] = None
    inputs: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

def list_prompt_templates() -> List[PromptTemplate]:
    """Return all prompt templates available on disk."""

    templates = []
    for data in prompt_loader.list_templates():
        try:
            templates.append(PromptTemplate(**data))
        except Exception:
            continue
    return templates

def get_prompt_template(tid: str) -> Optional[PromptTemplate]:
    """Return a single prompt template by ``tid`` if present."""

    data = prompt_loader.load_template(tid)
    if not data:
        return None
    return PromptTemplate(**data)
