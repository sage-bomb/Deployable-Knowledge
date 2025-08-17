import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

import app.main as main
from core import pipeline
from core.models import ChatResponse, Source
from core.prompts import renderer
from core.rag import retriever
from app.auth.session import SessionValidationMiddleware
from app.core.llm import provider


async def _bypass(self, request, call_next):
    return await call_next(request)


SessionValidationMiddleware.dispatch = _bypass

client = TestClient(main.app)


def test_chat_endpoint(monkeypatch):
    def fake_chat_once(req):
        return ChatResponse(text="hi", sources=[Source(id="1")], usage={})
    monkeypatch.setattr(pipeline, "chat_once", fake_chat_once)
    monkeypatch.setattr(renderer, "generate_title", lambda s: "title")
    monkeypatch.setattr(renderer, "update_summary", lambda old, u, a: "summary")
    sid = str(provider.list_services()[0].id)
    res = client.post(
        "/chat",
        data={
            "message": "hi",
            "session_id": "12345678-1234-1234-1234-123456789012",
            "service_id": sid,
        },
        cookies={"session": "test"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["response"]


def test_search_endpoint(monkeypatch):
    monkeypatch.setattr(retriever, "search", lambda q, top_k=5, exclude_sources=None: [{"text": "a"}])
    res = client.get("/search", params={"q": "test"}, cookies={"session": "test"})
    assert res.status_code == 200
    assert res.json()["results"]
