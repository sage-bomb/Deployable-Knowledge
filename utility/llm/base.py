from typing import Any, Iterator

class BaseLLM:
    """Minimal LLM interface the app expects."""
    def __init__(self, model: str | None = None, **kwargs: Any) -> None:
        self.model = model

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Return a full string completion."""
        raise NotImplementedError

    def stream_text(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Yield chunks of text for streaming UIs."""
        raise NotImplementedError
