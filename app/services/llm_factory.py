from typing import Optional
from app.llm.base import BaseLLM
from app.llm.ollama_llm import OllamaLLM
from app.llm.openai_llm import OpenAILLM

def make_llm(provider: str, model: Optional[str]) -> BaseLLM:
    if provider == "ollama":
        return OllamaLLM(model=model)
    if provider == "openai":
        return OpenAILLM(model=model)
    # Fallback to ollama
    return OllamaLLM(model=model)
