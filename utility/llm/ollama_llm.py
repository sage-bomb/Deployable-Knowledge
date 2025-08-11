import requests
from typing import Any
from .base import BaseLLM
from config import OLLAMA_BASE_URL, OLLAMA_MODEL  # add these if missing

class OllamaLLM(BaseLLM):
    def __init__(self, model: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        super().__init__(model=model or OLLAMA_MODEL)
        self.base_url = base_url or OLLAMA_BASE_URL

    def generate(self, prompt: str, **kwargs: Any) -> str:
        # Simple non-stream generate API
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False} | kwargs,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # 'response' is plain text for /api/generate
        return data.get("response", "")
