"""Filesystem backed store for :class:`ChatSession` objects."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from utility.chat_state import ChatSession
from utility.logger import get_logger


SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)

logger = get_logger(__name__)


class SessionStore:
    """Persist chat sessions as JSON files on disk."""

    def __init__(self, storage_path: Path = SESSION_DIR):
        self.storage_path = storage_path

    # ------------------------------------------------------------------
    def _session_path(self, session_id: str) -> Path:
        return self.storage_path / f"{session_id}.json"

    # ------------------------------------------------------------------
    def save(self, session: ChatSession) -> None:
        """Serialize ``session`` to disk."""

        with open(self._session_path(session.session_id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

    # ------------------------------------------------------------------
    def load(self, session_id: str) -> Optional[ChatSession]:
        """Load a session by identifier."""

        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ChatSession.from_dict(data)
        except json.JSONDecodeError:
            logger.warning("Corrupt session file for %s, deleting.", session_id)
            path.unlink()
            return None

    # ------------------------------------------------------------------
    def list_sessions(self) -> List[Dict]:
        return [
            {
                "id": f.stem,
                "path": str(f),
                "modified": f.stat().st_mtime,
            }
            for f in self.storage_path.glob("*.json")
        ]

    # ------------------------------------------------------------------
    def delete(self, session_id: str) -> None:
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    def exists(self, session_id: str) -> bool:
        return self._session_path(session_id).exists()
