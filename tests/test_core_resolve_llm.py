import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from types import SimpleNamespace
from uuid import uuid4

from core.prompts import renderer


def test_resolve_llm_uses_model_name(monkeypatch):
    sid = uuid4()
    mid = uuid4()
    service = SimpleNamespace(id=sid, provider="mock")
    model = SimpleNamespace(id=mid, name="ui-name", model_name="actual-model")

    monkeypatch.setattr(renderer.llm_provider, "list_services", lambda: [service])
    monkeypatch.setattr(renderer.llm_provider, "list_models", lambda s: [model])

    captured = {}

    def fake_make_llm(provider, model_name):
        captured["provider"] = provider
        captured["model_name"] = model_name

        class Dummy:
            def generate_text(self, prompt):
                return "ok"

            def stream_text(self, prompt):
                yield "ok"

        return Dummy()

    monkeypatch.setattr(renderer, "make_llm", fake_make_llm)

    renderer.ask_llm("hi", service_id=str(sid), model_id=str(mid))

    assert captured["model_name"] == "actual-model"
