# Prompt and LLM Integration

Prompt templates reside in the `prompts/` directory and can be listed or updated through the settings API.  Templates define a system prompt, user formatting and how retrieved context is embedded into the prompt.

`core/prompts/renderer.py` resolves the active template, renders context and history, then calls the selected LLM provider via `core/llm` factories.  Providers are chosen based on user settings (`ollama` by default).

Return to [docs](README.md).
