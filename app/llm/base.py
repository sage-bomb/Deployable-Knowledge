from typing import Any, Dict

class BaseLLM:
    def __init__(self, model: str | None = None, **kwargs: Any) -> None:
        self.model = model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return a string completion."""
        raise NotImplementedError
