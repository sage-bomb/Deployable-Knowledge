import uuid

from fastapi.testclient import TestClient
import app.main as main
from app.auth.session import SessionValidationMiddleware
from core.db import SessionLocal, User


async def _bypass(self, request, call_next):
    return await call_next(request)


SessionValidationMiddleware.dispatch = _bypass

client = TestClient(main.app)


def test_user_retrieval():
    user_id = f"test-{uuid.uuid4()}"
    email = f"{user_id}@example.com"
    with SessionLocal() as db:
        db.add(User(id=user_id, email=email, hashed_password="!"))
        db.commit()

    res = client.get(f"/api/users/{user_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == user_id
    assert data["email"] == email

    res = client.get("/api/users")
    assert res.status_code == 200
    users = res.json()
    assert any(u["id"] == user_id for u in users)

    res = client.get("/api/users/does-not-exist")
    assert res.status_code == 404
