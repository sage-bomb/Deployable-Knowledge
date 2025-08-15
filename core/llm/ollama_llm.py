from typing import Any, Iterator
import requests, json
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .base import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, model: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        self.base_url = base_url or OLLAMA_BASE_URL
        super().__init__(model or OLLAMA_MODEL)

    def _generate_url(self) -> str:
        return f"{self.base_url}/api/generate"

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        resp = requests.post(self._generate_url(), json=payload, timeout=kwargs.get("timeout", 120))
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")

    def stream_text(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        with requests.post(self._generate_url(), json=payload, stream=True, timeout=kwargs.get("timeout", None)) as r:
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
                    yield line
