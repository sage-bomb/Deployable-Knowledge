import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.models import ChatRequest
from core import pipeline


def test_chat_once_returns_sources(monkeypatch):
    monkeypatch.setattr(pipeline.renderer, "ask_llm", lambda prompt, user_id=None: "answer")
    monkeypatch.setattr(
        pipeline.retriever,
        "search",
        lambda q, top_k=8, exclude_sources=None: [{"text": "ctx", "source": "doc"}],
    )
    req = ChatRequest(message="hi", top_k=1)
    resp = pipeline.chat_once(req)
    assert resp.text == "answer"
    assert resp.sources and resp.sources[0].title == "doc"
