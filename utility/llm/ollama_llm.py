from typing import Any, Iterator
import requests, json
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .base import BaseLLM

GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

class OllamaLLM(BaseLLM):
    def __init__(self, model: str | None = None, **kwargs: Any) -> None:
        super().__init__(model or OLLAMA_MODEL)

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        resp = requests.post(GENERATE_URL, json=payload, timeout=kwargs.get("timeout", 120))
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    def stream_text(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        with requests.post(GENERATE_URL, json=payload, stream=True, timeout=kwargs.get("timeout", None)) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    chunk = obj.get("response", "")
                    if chunk:
                        yield chunk
                except Exception:
                    # Older ollama may emit plain text lines
                    yield line
