import sys, pathlib, shutil
from fastapi import FastAPI

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# Ensure fresh registry for tests
reg_dir = pathlib.Path(__file__).resolve().parents[1] / ".llm_registry"
if reg_dir.exists():
    shutil.rmtree(reg_dir)

from fastapi.testclient import TestClient
from app.routes.api_llm import router as llm_router

app = FastAPI()
app.include_router(llm_router)

client = TestClient(app)


def test_llm_registry_crud():
    # Initial services (seeded)
    res = client.get("/api/llm/services")
    assert res.status_code == 200
    base_count = len(res.json())

    # Create service
    payload = {"name": "test-svc", "provider": "custom"}
    res = client.post("/api/llm/services", json=payload)
    assert res.status_code == 201
    sid = res.json()["id"]

    # Create model
    model_payload = {
        "service_id": sid,
        "name": "test-model",
        "model_name": "test-model",
    }
    res = client.post("/api/llm/models", json=model_payload)
    assert res.status_code == 201
    mid = res.json()["id"]
    assert res.json()["model_name"] == "test-model"

    # Selection
    sel_payload = {"service_id": sid, "model_id": mid}
    res = client.put("/api/llm/selection", json=sel_payload)
    assert res.status_code == 200
    assert res.json()["user_id"] == "local-user"
    res = client.get("/api/llm/selection")
    assert res.json()["model_id"] == mid

    # Cascade delete service
    res = client.delete(f"/api/llm/services/{sid}")
    assert res.status_code == 200

    # Models for deleted service should be empty
    res = client.get("/api/llm/models", params={"service_id": sid})
    assert res.status_code == 200
    assert res.json() == []
