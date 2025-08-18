import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from core.models import ChatChunk, ChatResponse
from core import pipeline
from core.prompts import renderer
import app.main as main
from app.core.llm import provider

client = TestClient(main.app)


def test_sse_stream(monkeypatch):
    def fake_stream(req):
        yield ChatChunk(type="meta", text="{}")
        yield ChatChunk(type="delta", text="hi")
        yield ChatChunk(type="done", sources=[], usage={})

    monkeypatch.setattr(pipeline, "chat_stream", fake_stream)
    monkeypatch.setattr(renderer, "generate_title", lambda s: "title")
    monkeypatch.setattr(renderer, "update_summary", lambda old, u, a: "summary")

    sid = str(provider.list_services()[0].id)
    with client.stream(
        "POST",
        "/chat?stream=true",
        data={
            "message": "hi",
            "session_id": "12345678-1234-1234-1234-123456789012",
            "service_id": sid,
        },
        cookies={"session": "test"},
    ) as res:
        assert res.status_code == 200
        body = "".join(line.decode() if isinstance(line, bytes) else line for line in res.iter_lines())

    assert "event: meta" in body
    assert "event: delta" in body
    assert "event: done" in body


def test_model_id_forwarded(monkeypatch):
    captured = {}

    def fake_stream(req):
        captured["model_id"] = req.model_id
        yield ChatChunk(type="meta", text="{}")
        yield ChatChunk(type="done", sources=[], usage={})

    monkeypatch.setattr(pipeline, "chat_stream", fake_stream)
    monkeypatch.setattr(renderer, "generate_title", lambda s: "title")
    monkeypatch.setattr(renderer, "update_summary", lambda old, u, a: "summary")

    sid = provider.list_services()[0].id
    mid = str(provider.list_models(sid)[0].id)
    with client.stream(
        "POST",
        "/chat?stream=true",
        data={
            "message": "hi",
            "session_id": "12345678-1234-1234-1234-123456789012",
            "service_id": str(sid),
            "model_id": mid,
        },
        cookies={"session": "test"},
    ) as res:
        assert res.status_code == 200
        list(res.iter_lines())

    assert captured["model_id"] == mid


def test_stream_error_propagates(monkeypatch):
    def fake_stream(req):
        yield ChatChunk(type="error", text="bad model")

    monkeypatch.setattr(pipeline, "chat_stream", fake_stream)
    sid = str(provider.list_services()[0].id)
    with client.stream(
        "POST",
        "/chat?stream=true",
        data={
            "message": "hi",
            "session_id": "12345678-1234-1234-1234-123456789012",
            "service_id": sid,
        },
        cookies={"session": "test"},
    ) as res:
        assert res.status_code == 200
        body = "".join(
            line.decode() if isinstance(line, bytes) else line for line in res.iter_lines()
        )

    assert "event: error" in body
    assert "bad model" in body


def test_chat_error_response(monkeypatch):
    monkeypatch.setattr(
        pipeline, "chat_once", lambda req: ChatResponse(text="", sources=[], usage={}, error="bad model")
    )
    res = client.post(
        "/chat",
        data={
            "message": "hi",
            "session_id": "12345678-1234-1234-1234-123456789012",
        },
        cookies={"session": "test"},
    )
    assert res.status_code == 400
    assert res.json()["error"] == "bad model"
