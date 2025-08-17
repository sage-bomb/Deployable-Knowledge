from __future__ import annotations
from typing import List, Dict, Optional, Iterable
from dataclasses import dataclass
import json, re
from uuid import UUID

from config import PROMPTS_DIR
from core.sessions import ChatExchange
from core.settings import get_prompt_template, load_settings
from core.llm import make_llm
from app.core.llm import provider as llm_provider

@dataclass
class Template:
    id: str
    name: str
    system: str
    user_format: str
    context_item_format: str = "- {chunk}"
    context_header: str = "Relevant context:"
    context_join: str = "\n"
    persona_format: str = "Persona: {persona}"
    history_separator: str = "\n"
    include_history: bool = True

def _load_template(tid: Optional[str]) -> Template:
    """Resolve ``tid`` to a :class:`Template` instance."""

    tid = tid or "rag_chat"
    tmpl = get_prompt_template(tid)
    if tmpl is None:
        f = (PROMPTS_DIR / f"{tid}.json")
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
        else:
            data = {
                "id": "rag_chat",
                "name": "RAG Chat (default)",
                "system": "You are a concise, technical assistant. Answer using only the provided context when possible.",
                "user_format": "{user}",
                "context_item_format": "- {chunk} (source: {source})",
                "context_header": "Context:",
                "context_join": "\n",
                "persona_format": "Persona: {persona}",
                "history_separator": "\n",
                "include_history": True
            }
    else:
        data = {
            "id": tmpl.id,
            "name": tmpl.name,
            "system": getattr(tmpl, "system", "") or "",
            "user_format": getattr(tmpl, "user_format", "") or "{user}",
            "context_item_format": getattr(tmpl, "context_item_format", "") or "- {chunk}",
            "context_header": getattr(tmpl, "context_header", "") or "Context:",
            "context_join": getattr(tmpl, "context_join", "") or "\n",
            "persona_format": getattr(tmpl, "persona_format", "") or "Persona: {persona}",
            "history_separator": getattr(tmpl, "history_separator", "") or "\n",
            "include_history": bool(getattr(tmpl, "include_history", True)),
        }
    return Template(**data)

def _fmt_defaults(s: str, **kwargs) -> str:
    """Format ``s`` replacing ``{name|default}`` tokens with values."""

    def repl(m):
        name = m.group(1)
        default = m.group(2) if m.group(2) is not None else ""
        return str(kwargs.get(name, default))

    s = re.sub(r"\{([a-zA-Z0-9_]+)\|([^}]+)\}", repl, s)
    return s.format(**{k: kwargs.get(k, "") for k in kwargs})

def _render_context(t: Template, context_blocks: List[Dict]) -> str:
    """Render retrieved context blocks using the template's format."""

    if not context_blocks:
        return ""
    lines = []
    for b in context_blocks:
        lines.append(
            _fmt_defaults(
                t.context_item_format,
                chunk=b.get("text", b.get("chunk", "")),
                source=b.get("source", b.get("doc", "unknown")),
                score=b.get("score", ""),
            )
        )
    return t.context_header + "\n" + t.context_join.join(lines)

def _render_history(t: Template, history: List[ChatExchange]) -> str:
    """Render the chat history portion of the prompt."""

    if not t.include_history or not history:
        return ""
    lines = []
    for h in history:
        lines.append(f"User: {getattr(h, 'user', '')}")
        a = getattr(h, "assistant", None) or getattr(h, "llm_response", None) or ""
        if a:
            lines.append(f"Assistant: {a}")
    return t.history_separator.join(lines)

def build_prompt(
    summary: str,
    history: List[ChatExchange],
    user_message: str,
    context_blocks: List[Dict],
    persona: Optional[str] = None,
    template_id: Optional[str] = None,
) -> str:
    """Construct the final prompt string for the LLM."""

    t = _load_template(template_id)
    ctx = _render_context(t, context_blocks)
    hist = _render_history(t, history)
    persona_str = _fmt_defaults(t.persona_format, persona=persona) if persona else ""
    user_str = _fmt_defaults(t.user_format, user=user_message)
    blocks = [t.system]
    if persona_str:
        blocks.append(persona_str)
    if summary:
        blocks.append(f"Summary so far: {summary}")
    if hist:
        blocks.append(hist)
    if ctx:
        blocks.append(ctx)
    blocks.append(user_str)
    return "\n\n".join([b for b in blocks if b])

def _resolve_settings(user_id: Optional[str]):
    """Best-effort lookup of user settings falling back to defaults."""

    s = None
    if user_id:
        try:
            s = load_settings(user_id)
        except Exception:
            pass
    if s is None:
        try:
            s = load_settings("default")
        except Exception:
            pass
    return s


def _resolve_llm(service_id: Optional[str], user_id: Optional[str]):
    """Return an LLM instance based on service or user settings."""

    if service_id:
        try:
            sid = UUID(str(service_id))
            srv = next((s for s in llm_provider.list_services() if s.id == sid), None)
            if srv:
                model_name = None
                try:
                    mlist = llm_provider.list_models(sid)
                    if mlist:
                        model_name = mlist[0].name
                except Exception:
                    pass
                return make_llm(srv.provider, model_name)
        except Exception:
            pass
    s = _resolve_settings(user_id)
    provider = getattr(s, "llm_provider", "ollama")
    model = getattr(s, "llm_model", "") or None
    return make_llm(provider, model)

def stream_llm(
    prompt: str, user_id: Optional[str] = None, service_id: Optional[str] = None
) -> Iterable[str]:
    """Stream tokens from the configured LLM provider."""

    llm = _resolve_llm(service_id, user_id)
    return llm.stream_text(prompt)


def ask_llm(
    prompt: str, user_id: Optional[str] = None, service_id: Optional[str] = None
) -> str:
    """Return a complete text response from the LLM."""

    llm = _resolve_llm(service_id, user_id)
    return llm.generate_text(prompt)

def update_summary(old_summary: str, last_user: str, last_assistant: str, user_id: Optional[str]=None) -> str:
    """Use the LLM to generate an updated conversation summary."""

    instr = (
        "Update the running summary of this conversation. Keep it concise and factual.\n"
        f"Old summary: {old_summary}\n"
        f"Last user: {last_user}\n"
        f"Last assistant: {last_assistant}\n"
        "New concise summary:"
    )
    return ask_llm(instr, user_id=user_id)

def generate_title(first_interaction: str, user_id: Optional[str]=None) -> str:
    """Produce a short title summarising the chat session."""

    prompt = (
        f"{first_interaction}\n"
        "Given this chat interaction, provide a snappy short title we can use for it."
    )
    return (ask_llm(prompt, user_id=user_id) or "").strip()[:80]

