import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.prompts import renderer
from core.sessions import ChatExchange


def test_build_prompt_with_context_persona_history():
    history = [ChatExchange(user="hi", context_used=[], rag_prompt="", assistant="there", html_response="")]
    context = [{"text": "ctx", "source": "doc1"}]
    prompt = renderer.build_prompt(
        summary="sum",
        history=history,
        user_message="question",
        context_blocks=context,
        persona="friendly",
        template_id="rag_chat",
    )
    assert "friendly" in prompt
    assert "Summary so far: sum" in prompt
    assert "User: hi" in prompt and "Assistant: there" in prompt
    assert "ctx" in prompt
    assert "question" in prompt
