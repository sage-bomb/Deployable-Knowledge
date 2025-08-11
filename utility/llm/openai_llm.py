from typing import Any
from .base import BaseLLM

class OpenAILLM(BaseLLM):
    def generate(self, prompt: str, **kwargs: Any) -> str:
        # Intentionally empty skeleton. Wire OpenAI SDK later.
        # Return a placeholder so the app doesn't crash if misconfigured.
        return "[OpenAI LLM not configured]"
