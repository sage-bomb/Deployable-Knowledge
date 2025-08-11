from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable
from uuid import UUID


_FILENAME_CLEAN_PATTERN = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str, allowed_extensions: Iterable[str] | None = None) -> str:
    name = Path(filename).name
    name = _FILENAME_CLEAN_PATTERN.sub("_", name)
    if name in {"", ".", ".."}:
        raise ValueError("Invalid filename")
    if allowed_extensions is not None:
        ext = Path(name).suffix.lower()
        if ext not in {e.lower() for e in allowed_extensions}:
            raise ValueError(f"Unsupported file type: {ext}")
    return name


def validate_session_id(session_id: str) -> str:
    try:
        return str(UUID(session_id, version=4))
    except Exception as exc:
        raise ValueError("Invalid session id") from exc


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
