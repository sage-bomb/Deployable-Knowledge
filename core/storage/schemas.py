from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class User(BaseModel):
    """User account information."""

    id: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Authenticated user session."""

    id: str
    user_id: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    ua_hash: Optional[str] = None
    ip_net: Optional[str] = None
    attrs: dict = Field(default_factory=dict)


class Document(BaseModel):
    """Ingested document metadata."""

    id: str
    owner_id: str
    title: Optional[str] = None
    path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict = Field(default_factory=dict)


class Prompt(BaseModel):
    """Prompt template description."""

    id: str
    name: str
    description: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    """Single message within a chat history."""

    id: str
    user_id: str
    session_id: Optional[str] = None
    role: Literal["user", "assistant", "system"] = "user"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
