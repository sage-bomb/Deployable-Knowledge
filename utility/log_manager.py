from pathlib import Path
import json
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Optional

from config import LOG_DIR

class LogManager:
    def __init__(self, log_dir: Path = LOG_DIR):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.log_dir / f"{session_id}.json"

    def start_session(self, user_id: str) -> str:
        session_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + "-" + uuid4().hex[:8]
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "messages": []
        }
        self._session_path(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return session_id

    def append_message(self, session_id: str, role: str, text: str) -> None:
        path = self._session_path(session_id)
        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = {"session_id": session_id, "user_id": "unknown", "timestamp": datetime.utcnow().isoformat(), "messages": []}
        data.setdefault("messages", []).append({
            "role": role,
            "text": text,
            "time": datetime.utcnow().isoformat()
        })
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_sessions(self, user_id: str) -> List[Dict]:
        sessions = []
        for file in self.log_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                if data.get("user_id") == user_id:
                    sessions.append({"session_id": data.get("session_id"), "timestamp": data.get("timestamp")})
            except Exception:
                continue
        sessions.sort(key=lambda x: x.get("timestamp"), reverse=True)
        return sessions

    def load_session(self, session_id: str) -> Optional[Dict]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
