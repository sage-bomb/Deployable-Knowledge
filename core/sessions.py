"""Chat session models and persistence."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
import uuid

from core.db import SessionLocal, DBChatSession, DBChatExchange, chat_ops, User

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
    created_at: Optional[datetime] = None

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )
        session.history = [ChatExchange.from_dict(e) for e in data.get("history", [])]
        return session

class SessionStore:
    """Database-backed persistence for :class:`ChatSession` objects."""

    def save(self, session: ChatSession) -> None:
        """Persist ``session`` to the SQL database."""
        with SessionLocal() as db:
            db_sess = (
                db.query(DBChatSession).filter(DBChatSession.id == session.session_id).first()
            )
            if not db_sess:
                user = db.query(User).filter(User.id == session.user_id).first()
                if not user:
                    user = User(id=session.user_id, email=f"{session.user_id}@local", hashed_password="!")
                    db.add(user)
                    db.commit()
                db_sess = DBChatSession(
                    id=session.session_id,
                    user_id=session.user_id,
                    summary=session.summary,
                    title=session.title,
                    persona=session.persona,
                )
                db.add(db_sess)
                db.commit()
            else:
                db_sess.summary = session.summary
                db_sess.title = session.title
                db_sess.persona = session.persona
                db.commit()
            session.created_at = db_sess.created_at
            existing = (
                db.query(DBChatExchange)
                .filter(DBChatExchange.session_id == session.session_id)
                .count()
            )
            for ex in session.history[existing:]:
                chat_ops.add_chat_exchange(
                    db,
                    session_id=session.session_id,
                    user_message=ex.user,
                    rag_prompt=ex.rag_prompt,
                    assistant_message=ex.assistant,
                    html_response=ex.html_response,
                    context_used=ex.context_used,
                )

    def load(self, session_id: str) -> Optional[ChatSession]:
        """Load a session from the SQL database or return ``None`` if missing."""
        with SessionLocal() as db:
            db_sess = (
                db.query(DBChatSession).filter(DBChatSession.id == session_id).first()
            )
            if not db_sess:
                return None
            session = ChatSession(
                session_id=db_sess.id,
                user_id=db_sess.user_id,
                summary=db_sess.summary,
                title=db_sess.title,
                inactive_sources=[],
                persona=db_sess.persona,
                created_at=db_sess.created_at,
            )
            exchanges = chat_ops.list_chat_exchanges(db, session_id)
            for e in exchanges:
                session.history.append(
                    ChatExchange(
                        user=e.user_message,
                        context_used=e.context_used,
                        rag_prompt=e.rag_prompt,
                        assistant=e.assistant_message,
                        html_response=e.html_response,
                    )
                )
            return session

    def list_sessions(self) -> List[Dict]:
        """Return metadata for all stored sessions."""
        with SessionLocal() as db:
            sessions = db.query(DBChatSession).all()
            return [
                {"id": s.id, "created": s.created_at.timestamp()}
                for s in sessions
            ]

    def delete(self, session_id: str) -> None:
        """Remove ``session_id`` from the database."""
        with SessionLocal() as db:
            chat_ops.delete_chat_session(db, session_id)

    def exists(self, session_id: str) -> bool:
        """Return ``True`` if a session exists in the database."""
        with SessionLocal() as db:
            return (
                db.query(DBChatSession).filter(DBChatSession.id == session_id).first()
                is not None
            )

    def prune_empty(self) -> None:
        """Delete any chat sessions that contain no exchanges."""
        with SessionLocal() as db:
            sessions = db.query(DBChatSession).all()
            for s in sessions:
                if not s.exchanges:
                    db.delete(s)
            db.commit()
