import uuid
from pathlib import Path

from core import settings


def test_model_specific_settings_persist(tmp_path):
    user_id = f"test-{uuid.uuid4()}"
    file_path = settings.USERS_DIR / f"{user_id}.json"
    if file_path.exists():
        file_path.unlink()
    s = settings.load_settings(user_id)
    assert s.ollama.model == ""
    patch = {
        "ollama": {"model": "llama2", "host": "http://1.2.3.4:11434"},
        "openai": {"model": "gpt-4", "api_key": "sk-test"},
    }
    settings.update_settings(user_id, patch)
    s2 = settings.load_settings(user_id)
    assert s2.ollama.model == "llama2"
    assert s2.ollama.host == "http://1.2.3.4:11434"
    assert s2.openai.model == "gpt-4"
    assert s2.openai.api_key == "sk-test"
    file_path.unlink()
