from typing import Any, Iterator
from .base import BaseLLM

class OpenAILLM(BaseLLM):
    """Placeholder OpenAI backend. Wire the SDK when ready."""
    def __init__(self, model: str | None = None, **kwargs: Any) -> None:
        super().__init__(model or "gpt-4o-mini")

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        return "[OpenAI LLM not configured]"

    def stream_text(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        yield self.generate_text(prompt, **kwargs)
