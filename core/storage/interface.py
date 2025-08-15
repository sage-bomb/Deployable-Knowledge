from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .schemas import User, Session, Document, Prompt, ChatMessage


class StorageBackend(ABC):
    """Abstract interface describing persistence operations."""

    # Users
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    def save_user(self, user: User) -> None: ...

    @abstractmethod
    def delete_user(self, user_id: str) -> None: ...

    # Sessions
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]: ...

    @abstractmethod
    def save_session(self, session: Session) -> None: ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None: ...

    # Documents
    @abstractmethod
    def list_documents(self, owner_id: Optional[str] = None) -> List[Document]: ...

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Document]: ...

    @abstractmethod
    def save_document(self, doc: Document) -> None: ...

    @abstractmethod
    def delete_document(self, doc_id: str) -> None: ...

    # Prompts
    @abstractmethod
    def list_prompts(self, owner_id: Optional[str] = None) -> List[Prompt]: ...

    @abstractmethod
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]: ...

    @abstractmethod
    def save_prompt(self, prompt: Prompt) -> None: ...

    @abstractmethod
    def delete_prompt(self, prompt_id: str) -> None: ...

    # Chat history
    @abstractmethod
    def append_chat_message(self, message: ChatMessage) -> None: ...

    @abstractmethod
    def get_chat_history(self, user_id: str, limit: Optional[int] = None) -> List[ChatMessage]: ...

    @abstractmethod
    def clear_chat_history(self, user_id: str) -> None: ...
