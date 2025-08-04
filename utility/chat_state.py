"""Chat session and exchange data models.

This module defines lightweight data containers used to persist chat
history and session level metadata.  The previous implementation used
ad-hoc classes with a mixture of attribute names (e.g. ``llm_response``)
which made it difficult to work with the objects consistently.  The
refactored version below leverages :mod:`dataclasses` to provide a
clear, typed structure and introduces a single ``assistant`` field for
LLM responses.  For backwards compatibility the loader understands the
old ``llm_response`` key.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ChatExchange:
    """Represents a single interaction within a chat session."""

    user: str
    context_used: List[Dict]
    rag_prompt: str
    assistant: str
    html_response: str

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "user": self.user,
            "context_used": self.context_used,
            "rag_prompt": self.rag_prompt,
            "assistant": self.assistant,
            "html_response": self.html_response,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatExchange":
        """Create an exchange from serialized data.

        Both ``assistant`` and the legacy ``llm_response`` keys are
        supported when restoring older session files.
        """

        return cls(
            user=data.get("user", ""),
            context_used=data.get("context_used", []),
            rag_prompt=data.get("rag_prompt", ""),
            assistant=data.get("assistant") or data.get("llm_response", ""),
            html_response=data.get("html_response", ""),
        )


@dataclass
class ChatSession:
    """Container for a user's ongoing chat session."""

    session_id: str
    history: List[ChatExchange] = field(default_factory=list)
    summary: str = ""
    inactive_sources: List[str] = field(default_factory=list)
    persona: Optional[str] = None

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def new(cls, session_id: Optional[str] = None) -> "ChatSession":
        """Create a new chat session with a random identifier."""

        return cls(session_id=session_id or str(uuid.uuid4()))

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def add_exchange(
        self,
        user: str,
        context_used: List[Dict],
        rag_prompt: str,
        assistant: str,
        html_response: str,
    ) -> None:
        """Append a new exchange to the session history."""

        self.history.append(
            ChatExchange(
                user=user,
                context_used=context_used,
                rag_prompt=rag_prompt,
                assistant=assistant,
                html_response=html_response,
            )
        )

    def trim_history(self, max_length: int) -> None:
        """Keep only the most recent ``max_length`` exchanges."""

        if len(self.history) > max_length:
            self.history = self.history[-max_length:]

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "summary": self.summary,
            "history": [exchange.to_dict() for exchange in self.history],
            "inactive_sources": self.inactive_sources,
            "persona": self.persona,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatSession":
        session = cls(
            session_id=data.get("session_id", ""),
            summary=data.get("summary", ""),
            inactive_sources=data.get("inactive_sources", []),
            persona=data.get("persona"),
        )
        session.history = [ChatExchange.from_dict(e) for e in data.get("history", [])]
        return session

