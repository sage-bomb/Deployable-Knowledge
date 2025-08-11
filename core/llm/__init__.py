from typing import Optional
from .base import BaseLLM
from .ollama_llm import OllamaLLM
from .openai_llm import OpenAILLM
import os

DEFAULT_PROVIDER = "ollama"

def make_llm(provider: str, model: Optional[str]) -> BaseLLM:
    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return OpenAILLM(model=model)
    if provider == "openai":
        return OpenAILLM(model=model)
    return OllamaLLM(model=model)
