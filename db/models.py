"""SQLAlchemy ORM models for persistent application data.

These models mirror the various pieces of information that are currently stored
on disk.  They will eventually replace the JSON and flat‑file based storage once
migration to a database is complete.
"""
from __future__ import annotations

from datetime import datetime
import uuid
from typing import List

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from . import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: str = Column(String, primary_key=True, default=_uuid)
    email: str = Column(String, unique=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    llm_config = Column(JSON, default=dict)

    sessions: List["WebSession"] = relationship("WebSession", back_populates="user")
    chat_sessions: List["ChatSession"] = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )


class WebSession(Base):
    """Browser session used by the HTTPS web interface."""

    __tablename__ = "web_sessions"

    session_id: str = Column(String, primary_key=True)
    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    issued_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: datetime = Column(DateTime, nullable=False)
    last_seen: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    ua_hash: str | None = Column(String, nullable=True)
    ip_net: str | None = Column(String, nullable=True)
    attrs = Column(JSON, default=dict)

    user = relationship("User", back_populates="sessions")


class ChatSession(Base):
    """Conversation history for a user."""

    __tablename__ = "chat_sessions"

    id: str = Column(String, primary_key=True, default=_uuid)
    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    summary: str = Column(Text, default="")
    title: str = Column(String, default="")
    persona: str | None = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    exchanges: List["ChatExchange"] = relationship(
        "ChatExchange", back_populates="session", cascade="all, delete-orphan"
    )


class ChatExchange(Base):
    """Individual turn within a chat session."""

    __tablename__ = "chat_exchanges"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    session_id: str = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    user_message: str = Column(Text)
    rag_prompt: str = Column(Text)
    assistant_message: str = Column(Text)
    html_response: str = Column(Text)
    context_used = Column(JSON, default=list)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="exchanges")


class PromptTemplate(Base):
    """Prompt templates loaded by the application."""

    __tablename__ = "prompts"

    id: str = Column(String, primary_key=True)
    name: str = Column(String, unique=True, nullable=False)
    content = Column(JSON, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Metadata for user provided documents."""

    __tablename__ = "documents"

    id: str = Column(String, primary_key=True, default=_uuid)
    filename: str = Column(String, nullable=False)
    path: str = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    uploaded_at: datetime = Column(DateTime, default=datetime.utcnow)
