from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict
import json
from config import PROMPTS_DIR


def load_template(tid: str) -> Optional[Dict]:
    """Load a prompt template by identifier."""

    f = PROMPTS_DIR / f"{tid}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_templates() -> List[Dict]:
    """Return all available prompt templates as dictionaries."""

    out: List[Dict] = []
    for f in PROMPTS_DIR.glob("*.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out
