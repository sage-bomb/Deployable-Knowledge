"""Chat session models and persistence."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import uuid
import json
from pathlib import Path

# --- Chat history models ---

@dataclass
class ChatExchange:
    """Single turn of chat history."""

    user: str
    context_used: List[Dict]
    rag_prompt: str
    assistant: str
    html_response: str

    def to_dict(self) -> Dict:
        """Serialise the exchange to a dictionary."""

        return {
            "user": self.user,
            "context_used": self.context_used,
            "rag_prompt": self.rag_prompt,
            "assistant": self.assistant,
            "html_response": self.html_response,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatExchange":
        """Construct an exchange from stored JSON data."""

        return cls(
            user=data.get("user", ""),
            context_used=data.get("context_used", []),
            rag_prompt=data.get("rag_prompt", ""),
            assistant=data.get("assistant") or data.get("llm_response", ""),
            html_response=data.get("html_response", ""),
        )

@dataclass
class ChatSession:
    """Mutable container for a user's conversation history."""

    session_id: str
    user_id: str = "default"
    history: List[ChatExchange] = field(default_factory=list)
    summary: str = ""
    title: str = ""
    inactive_sources: List[str] = field(default_factory=list)
    persona: Optional[str] = None

    @classmethod
    def new(cls, session_id: Optional[str] = None, user_id: str = "default") -> "ChatSession":
        """Create a new session with a unique identifier."""

        return cls(session_id=session_id or str(uuid.uuid4()), user_id=user_id)

    def add_exchange(self, user: str, context_used: List[Dict], rag_prompt: str, assistant: str, html_response: str) -> None:
        """Append a chat exchange to the history."""

        self.history.append(ChatExchange(user, context_used, rag_prompt, assistant, html_response))

    def trim_history(self, max_length: int) -> None:
        """Limit history length to ``max_length`` items."""

        if len(self.history) > max_length:
            self.history = self.history[-max_length:]

    def to_dict(self) -> Dict:
        """Serialise the session for storage."""

        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "summary": self.summary,
            "title": self.title,
            "history": [h.to_dict() for h in self.history],
            "inactive_sources": self.inactive_sources,
            "persona": self.persona,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatSession":
        """Rehydrate a session from stored JSON data."""

        session = cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", "default"),
            summary=data.get("summary", ""),
            title=data.get("title", ""),
            inactive_sources=data.get("inactive_sources", []),
            persona=data.get("persona"),
        )
        session.history = [ChatExchange.from_dict(e) for e in data.get("history", [])]
        return session

# --- Session store ---

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)

class SessionStore:
    """Simple file-based persistence for :class:`ChatSession` objects."""

    def __init__(self, storage_path: Path = SESSION_DIR):
        self.storage_path = storage_path

    def _session_path(self, session_id: str) -> Path:
        """Return the filesystem path for ``session_id``."""

        return self.storage_path / f"{session_id}.json"

    def save(self, session: ChatSession) -> None:
        """Persist ``session`` to disk."""

        with open(self._session_path(session.session_id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

    def load(self, session_id: str) -> Optional[ChatSession]:
        """Load a session from disk or return ``None`` if missing."""

        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ChatSession.from_dict(data)
        except json.JSONDecodeError:
            path.unlink()
            return None

    def list_sessions(self) -> List[Dict]:
        """Return metadata for all stored sessions."""

        entries = []
        for f in self.storage_path.glob("*.json"):
            entries.append(
                {
                    "id": f.stem,
                    "path": str(f),
                    "modified": f.stat().st_mtime,
                }
            )
        return entries

    def delete(self, session_id: str) -> None:
        """Remove the on-disk file for ``session_id`` if it exists."""

        p = self._session_path(session_id)
        if p.exists():
            p.unlink()

    def exists(self, session_id: str) -> bool:
        """Return ``True`` if a session file exists."""

        return self._session_path(session_id).exists()

    def prune_empty(self) -> None:
        """Delete any session files that contain no history."""

        for entry in list(self.list_sessions()):
            session = self.load(entry["id"])
            if session and not session.history:
                self.delete(entry["id"])
