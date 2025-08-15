from typing import Optional
from .base import BaseLLM
from .ollama_llm import OllamaLLM
from .openai_llm import OpenAILLM

DEFAULT_PROVIDER = "ollama"

def make_llm(provider: str, model: Optional[str], **kwargs) -> BaseLLM:
    if provider == "openai":
        return OpenAILLM(model=model, api_key=kwargs.get("api_key"))
    return OllamaLLM(model=model, base_url=kwargs.get("base_url"))
