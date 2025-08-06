"""Simple session state management for sandbox testing.

This module uses module-level state to simulate the session ID behavior of a
larger application. It intentionally avoids any external dependencies or
frameworks so that the logic can be debugged in isolation.
"""

from __future__ import annotations

import uuid

# Internal storage for the current session ID.  The value is ``None`` until a
# session is explicitly started or set.
_session_id: str | None = None

def setSessionId(session_id: str) -> None:
    """Explicitly set the active session ID.

    Parameters
    ----------
    session_id:
        The identifier to mark as the current session.
    """
    global _session_id
    _session_id = session_id

def getSessionId() -> str | None:
    """Return the current session ID if one has been set."""
    return _session_id

def startNewSession() -> str:
    """Start a new session and return its identifier.

    The new ID is generated using :func:`uuid.uuid4` from Python's standard
    library.  In the real application this might trigger more complex startup
    logic, but for debugging purposes we only store and return the new ID.
    """
    global _session_id
    _session_id = str(uuid.uuid4())
    return _session_id
