from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable
from uuid import UUID


_FILENAME_CLEAN_PATTERN = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str, allowed_extensions: Iterable[str] | None = None) -> str:
    """Return a filesystem-safe version of ``filename``.

    Parameters
    ----------
    filename:
        Original filename supplied by the user.
    allowed_extensions:
        Optional iterable of permitted file extensions.  If provided the
        extension of ``filename`` must be one of these values.

    Returns
    -------
    str
        Sanitised filename with any unsafe characters replaced by underscores.

    Raises
    ------
    ValueError
        If the filename is invalid or the extension is not allowed.
    """

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
    """Validate that ``session_id`` is a UUID4 string.

    Parameters
    ----------
    session_id:
        The session identifier to validate.

    Returns
    -------
    str
        Normalised session ID string if valid.

    Raises
    ------
    ValueError
        If the provided session ID is not a valid UUID4.
    """

    try:
        return str(UUID(session_id, version=4))
    except Exception as exc:
        raise ValueError("Invalid session id") from exc


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    """Clamp ``value`` to the inclusive ``[minimum, maximum]`` range."""

    return max(minimum, min(maximum, value))
