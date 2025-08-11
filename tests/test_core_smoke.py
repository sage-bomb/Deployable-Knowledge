import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.models import ChatRequest
from core import pipeline


def test_chat_once(monkeypatch):
    def fake_ask(prompt, user_id=None):
        return "ok"
    monkeypatch.setattr(pipeline.renderer, "ask_llm", fake_ask)
    monkeypatch.setattr(
        pipeline.retriever, "search", lambda q, top_k=8, exclude_sources=None: []
    )
    req = ChatRequest(message="hi", top_k=0)
    resp = pipeline.chat_once(req)
    assert resp.text == "ok"


def test_chat_stream(monkeypatch):
    def fake_stream(prompt, user_id=None):
        yield "a"
        yield "b"
    monkeypatch.setattr(pipeline.renderer, "stream_llm", fake_stream)
    monkeypatch.setattr(
        pipeline.retriever, "search", lambda q, top_k=8, exclude_sources=None: []
    )
    req = ChatRequest(message="hi", top_k=0)
    chunks = list(pipeline.chat_stream(req))
    assert chunks[0].type == "meta"
    assert any(c.type == "delta" for c in chunks)
    assert chunks[-1].type == "done"
