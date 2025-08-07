import requests
import json
from typing import List, Dict, Optional
import markdown2

from config import OLLAMA_URL, OLLAMA_MODEL
from utility.chat_state import ChatExchange


def build_prompt(
    summary: str,
    history: List[ChatExchange],
    user_message: str,
    context_blocks: List[Dict],
    persona: Optional[str] = None
) -> str:
    history_block = "\n".join(
        f"User: {ex.user}\nAssistant: {ex.assistant}" for ex in history[-3:]
    )

    context_string = "\n\n".join(
        f"[{i+1}] {block['text']}" for i, block in enumerate(context_blocks)
    )
    persona_block = f"\n\n{persona.strip()}" if persona else ""

    return f"""You are a helpful assistant.

Summary of conversation so far:
{summary}

Recent conversation:
{history_block}

Context:
{context_string}{persona_block}

User: {user_message}
Assistant:"""


def call_llm(prompt: str, model: str = OLLAMA_MODEL) -> str:
    try:
        response = requests.post(OLLAMA_URL, json={"model": model, "prompt": prompt})
        return response.json().get("response", "[Error: No response]")
    except Exception as e:
        return f"[Error calling LLM: {str(e)}]"


def stream_llm(prompt: str, model: str = OLLAMA_MODEL):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True
        )
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("done"):
                    break
                if "response" in data:
                    yield data["response"]
            except json.JSONDecodeError:
                continue
    except Exception as e:
        yield f"[Streaming error: {str(e)}]"


def render_response_html(text: str) -> str:
    return markdown2.markdown(text, extras=[
        "fenced-code-blocks", "strike", "tables", "cuddled-lists"
    ])


def update_summary(old_summary: str, user_msg: str, assistant_msg: str) -> str:
    prompt = f"""
    [INST] You are a summarizer. Here is the existing summary of a conversation:
    {old_summary}

    Here is the new exchange:
    User: {user_msg}
    Assistant: {assistant_msg}

    Update the summary to include the new exchange. [/INST]
    """.strip()
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        })
        return response.json().get("response", old_summary)
    except Exception:
        return old_summary


def generate_title(first_interaction: str) -> str:
    """Return a short title for the chat based on the first exchange."""
    prompt = (
        f"{first_interaction}\n"
        "Given this chat interaction, provide a snappy short title we can use for it."
    )
    try:
        response = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt})
        return response.json().get("response", "").strip()
    except Exception:
        return first_interaction[:60]
