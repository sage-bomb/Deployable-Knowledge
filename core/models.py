from __future__ import annotations
from typing import List, Optional, Dict, Iterator, Literal
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Metadata describing a retrieved document fragment."""

    id: str
    title: Optional[str] = None
    filepath: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None


class ContextChunk(BaseModel):
    """A piece of text returned from retrieval along with its origin."""

    text: str
    source: Optional[Source] = None
    score: Optional[float] = None


class ChatRequest(BaseModel):
    """Parameters controlling a single chat turn."""

    user_id: Optional[str] = None
    service_id: Optional[str] = None
    model_id: Optional[str] = None
    message: str
    template_id: str = "rag_chat"
    top_k: int = 8
    persona: Optional[str] = None
    stream: bool = True
    inactive_sources: Optional[List[str]] = None


class ChatChunk(BaseModel):
    """Chunk of data streamed back to the client."""

    type: Literal["meta", "delta", "done", "error"]
    text: Optional[str] = None
    sources: Optional[List[Source]] = None
    usage: Optional[Dict[str, int]] = None


class ChatResponse(BaseModel):
    """Final chat response from the pipeline."""

    text: str
    sources: List[Source] = Field(default_factory=list)
    usage: Dict[str, int] = Field(default_factory=dict)
    error: Optional[str] = None
