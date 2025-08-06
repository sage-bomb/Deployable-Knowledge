"""Input validation utilities for file uploads and session handling."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from uuid import UUID

# Characters allowed in filenames. Anything else will be replaced with "_".
_FILENAME_CLEAN_PATTERN = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str, allowed_extensions: Iterable[str] | None = None) -> str:
    """Return a safe filename stripped of path components.

    Parameters
    ----------
    filename:
        Raw filename provided by the client.
    allowed_extensions:
        Optional iterable of lowercase extensions (including the dot) that
        the filename must match. If provided and the filename's extension is
        not in the set, :class:`ValueError` is raised.
    """
    name = Path(filename).name  # drop any directory components
    name = _FILENAME_CLEAN_PATTERN.sub("_", name)
    if name in {"", ".", ".."}:
        raise ValueError("Invalid filename")
    if allowed_extensions is not None:
        ext = Path(name).suffix.lower()
        if ext not in {e.lower() for e in allowed_extensions}:
            raise ValueError(f"Unsupported file type: {ext}")
    return name


def validate_session_id(session_id: str) -> str:
    """Validate that ``session_id`` is a UUID4 string.

    Raises ``ValueError`` if the session ID is malformed.
    Returns the normalized string form if valid.
    """
    try:
        return str(UUID(session_id, version=4))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Invalid session id") from exc


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    """Clamp ``value`` to the inclusive ``[minimum, maximum]`` range."""
    return max(minimum, min(maximum, value))
