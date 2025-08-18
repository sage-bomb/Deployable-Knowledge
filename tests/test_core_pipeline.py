import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.models import ChatRequest
from core import pipeline


def test_chat_once_returns_sources(monkeypatch):
    monkeypatch.setattr(
        pipeline.renderer,
        "ask_llm",
        lambda prompt, user_id=None, service_id=None, model_id=None: "answer",
    )
    monkeypatch.setattr(
        pipeline.retriever,
        "search",
        lambda q, top_k=8, exclude_sources=None: [{"text": "ctx", "source": "doc"}],
    )
    req = ChatRequest(message="hi", top_k=1)
    resp = pipeline.chat_once(req)
    assert resp.text == "answer"
    assert resp.sources and resp.sources[0].title == "doc"


def test_chat_once_forwards_model_id(monkeypatch):
    seen = {}

    def fake_ask(prompt, user_id=None, service_id=None, model_id=None):
        seen["model_id"] = model_id
        return "ok"

    monkeypatch.setattr(pipeline.renderer, "ask_llm", fake_ask)
    monkeypatch.setattr(
        pipeline.retriever,
        "search",
        lambda q, top_k=8, exclude_sources=None: [],
    )
    req = ChatRequest(message="hi", top_k=0, service_id="svc", model_id="model123")
    pipeline.chat_once(req)
    assert seen["model_id"] == "model123"


def test_chat_once_error(monkeypatch):
    monkeypatch.setattr(pipeline.retriever, "search", lambda *a, **k: [])

    def fake_ask(prompt, user_id=None, service_id=None, model_id=None):
        raise ValueError("bad model")

    monkeypatch.setattr(pipeline.renderer, "ask_llm", fake_ask)
    req = ChatRequest(message="hi")
    resp = pipeline.chat_once(req)
    assert resp.error == "bad model"


def test_chat_stream_error(monkeypatch):
    monkeypatch.setattr(pipeline.retriever, "search", lambda *a, **k: [])

    def fake_stream(prompt, user_id=None, service_id=None, model_id=None):
        raise ValueError("bad model")

    monkeypatch.setattr(pipeline.renderer, "stream_llm", fake_stream)
    req = ChatRequest(message="hi")
    chunks = list(pipeline.chat_stream(req))
    assert len(chunks) == 2
    assert chunks[0].type == "meta"
    assert chunks[1].type == "error"
    assert chunks[1].text == "bad model"
