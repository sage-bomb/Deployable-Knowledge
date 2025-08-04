import uuid
from typing import List, Optional


class ChatExchange:
    def __init__(
        self,
        user: str,
        context_used: List[dict],
        rag_prompt: str,
        llm_response: str,
        html_response: str
    ):
        self.user = user
        self.context_used = context_used
        self.rag_prompt = rag_prompt
        self.llm_response = llm_response
        self.html_response = html_response

    def to_dict(self):
        return {
            "user": self.user,
            "context_used": self.context_used,
            "rag_prompt": self.rag_prompt,
            "llm_response": self.llm_response,
            "html_response": self.html_response
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user=data["user"],
            context_used=data.get("context_used", []),
            rag_prompt=data.get("rag_prompt", ""),
            llm_response=data.get("llm_response", ""),
            html_response=data.get("html_response", "")
        )


class ChatSession:
    def __init__(
        self,
        session_id: str,
        history: Optional[List[ChatExchange]] = None,
        summary: str = "",
        inactive_sources: Optional[List[str]] = None,
        persona: Optional[str] = None
    ):
        self.session_id = session_id
        self.history = history or []
        self.summary = summary
        self.inactive_sources = inactive_sources or []
        self.persona = persona

    def add_exchange(self, user, context_used, rag_prompt, llm_response, html_response):
        self.history.append(ChatExchange(
            user=user,
            context_used=context_used,
            rag_prompt=rag_prompt,
            llm_response=llm_response,
            html_response=html_response
        ))

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "summary": self.summary,
            "history": [exchange.to_dict() for exchange in self.history],
            "inactive_sources": self.inactive_sources,
            "persona": self.persona
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(
            session_id=data["session_id"],
            summary=data.get("summary", ""),
            inactive_sources=data.get("inactive_sources", []),
            persona=data.get("persona")
        )
        session.history = [ChatExchange.from_dict(e) for e in data.get("history", [])]
        return session

    @classmethod
    def new(cls, session_id=None):
        return cls(session_id=session_id or str(uuid.uuid4()))
