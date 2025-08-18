from __future__ import annotations
from typing import Iterator, List
import json

from .models import ChatRequest, ChatResponse, ChatChunk, Source
from .prompts import renderer
from .rag import retriever


def _to_sources(blocks: List[dict]) -> List[Source]:
    """Convert raw retrieval blocks into :class:`Source` objects."""

    out: List[Source] = []
    for i, b in enumerate(blocks):
        out.append(
            Source(
                id=str(i),
                title=b.get("source"),
                filepath=b.get("source"),
                page=b.get("page"),
                score=b.get("score"),
            )
        )
    return out


def chat_once(req: ChatRequest) -> ChatResponse:
    """Execute a full chat turn and return the complete response."""
    try:
        context = retriever.search(
            req.message,
            top_k=req.top_k,
            exclude_sources=set(req.inactive_sources or []),
        )
        prompt = renderer.build_prompt(
            summary="",
            history=[],
            user_message=req.message,
            context_blocks=context,
            persona=req.persona,
            template_id=req.template_id,
        )
        text = renderer.ask_llm(
            prompt, user_id=req.user_id, service_id=req.service_id, model_id=req.model_id
        )
        return ChatResponse(text=text, sources=_to_sources(context), usage={})
    except Exception as e:
        return ChatResponse(text="", sources=[], usage={}, error=str(e))


def chat_stream(req: ChatRequest) -> Iterator[ChatChunk]:
    """Yield chat response chunks as they are produced by the LLM."""
    try:
        context = retriever.search(
            req.message,
            top_k=req.top_k,
            exclude_sources=set(req.inactive_sources or []),
        )
        prompt = renderer.build_prompt(
            summary="",
            history=[],
            user_message=req.message,
            context_blocks=context,
            persona=req.persona,
            template_id=req.template_id,
        )
        meta = json.dumps({"top_k": req.top_k, "template": req.template_id})
        yield ChatChunk(type="meta", text=meta)
        for token in renderer.stream_llm(
            prompt, user_id=req.user_id, service_id=req.service_id, model_id=req.model_id
        ):
            yield ChatChunk(type="delta", text=token)
        yield ChatChunk(type="done", sources=_to_sources(context), usage={})
    except Exception as e:
        yield ChatChunk(type="error", text=str(e))
