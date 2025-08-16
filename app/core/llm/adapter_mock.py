import json
import os
from pathlib import Path
from uuid import uuid4, UUID
from datetime import datetime
from typing import List

from .schemas import (
    LLMService,
    ServiceCreate,
    ServiceUpdate,
    LLMModel,
    ModelCreate,
    ModelUpdate,
    LLMSelection,
)

REGISTRY_DIR = Path(".llm_registry")
SERVICES_FILE = REGISTRY_DIR / "services.json"
MODELS_FILE = REGISTRY_DIR / "models.json"
SELECTION_FILE = REGISTRY_DIR / "selection.json"

services: List[LLMService] = []
models: List[LLMModel] = []
selections: dict[str, LLMSelection] = {}


def _serialize(obj):
    data = obj.model_dump()
    if "id" in data and data["id"]:
        data["id"] = str(data["id"])
    if "service_id" in data and data["service_id"]:
        data["service_id"] = str(data["service_id"])
    if "created_at" in data and data["created_at"]:
        data["created_at"] = obj.created_at.isoformat()  # type: ignore[attr-defined]
    return data


def _load():
    REGISTRY_DIR.mkdir(exist_ok=True)
    if SERVICES_FILE.exists():
        raw = json.loads(SERVICES_FILE.read_text())
        for item in raw:
            if item.get("created_at"):
                item["created_at"] = datetime.fromisoformat(item["created_at"])
            services.append(LLMService(**item))
    if MODELS_FILE.exists():
        raw = json.loads(MODELS_FILE.read_text())
        for item in raw:
            if item.get("created_at"):
                item["created_at"] = datetime.fromisoformat(item["created_at"])
            models.append(LLMModel(**item))
    if SELECTION_FILE.exists():
        raw = json.loads(SELECTION_FILE.read_text())
        for uid, item in raw.items():
            selections[uid] = LLMSelection(
                user_id=uid,
                service_id=UUID(item["service_id"]) if item.get("service_id") else None,
                model_id=UUID(item["model_id"]) if item.get("model_id") else None,
            )
    if not services:
        _seed()


def _save_services():
    REGISTRY_DIR.mkdir(exist_ok=True)
    SERVICES_FILE.write_text(json.dumps([_serialize(s) for s in services]))


def _save_models():
    REGISTRY_DIR.mkdir(exist_ok=True)
    MODELS_FILE.write_text(json.dumps([_serialize(m) for m in models]))


def _save_selection():
    REGISTRY_DIR.mkdir(exist_ok=True)
    data = {}
    for uid, sel in selections.items():
        data[uid] = {
            "service_id": str(sel.service_id) if sel.service_id else None,
            "model_id": str(sel.model_id) if sel.model_id else None,
        }
    SELECTION_FILE.write_text(json.dumps(data))


def _seed():
    openai_service = LLMService(
        id=uuid4(),
        name="openai-prod",
        provider="openai",
        created_at=datetime.utcnow(),
    )
    ollama_service = LLMService(
        id=uuid4(),
        name="ollama-local",
        provider="ollama",
        created_at=datetime.utcnow(),
    )
    services.extend([openai_service, ollama_service])
    models.append(
        LLMModel(
            id=uuid4(),
            service_id=openai_service.id,
            name="gpt-4o",
            created_at=datetime.utcnow(),
        )
    )
    models.append(
        LLMModel(
            id=uuid4(),
            service_id=ollama_service.id,
            name="llama3:8b",
            created_at=datetime.utcnow(),
        )
    )
    _save_services()
    _save_models()


_load()


# --- service operations ---

def list_services() -> List[LLMService]:
    return services


def create_service(data: ServiceCreate) -> LLMService:
    for s in services:
        if s.name == data.name:
            raise ValueError("service name must be unique")
    srv = LLMService(
        id=uuid4(),
        name=data.name,
        provider=data.provider,
        base_url=str(data.base_url) if data.base_url else None,
        auth_ref=data.auth_ref,
        timeout_sec=data.timeout_sec,
        is_enabled=data.is_enabled,
        extra=data.extra or {},
        created_at=datetime.utcnow(),
    )
    services.append(srv)
    _save_services()
    return srv


def update_service(sid: UUID, patch: ServiceUpdate) -> LLMService:
    for s in services:
        if s.id == sid:
            if patch.name and any(other.name == patch.name and other.id != sid for other in services):
                raise ValueError("service name must be unique")
            update = s.model_copy(update=patch.model_dump(exclude_unset=True))
            services[services.index(s)] = update
            _save_services()
            return update
    raise KeyError("service not found")


def delete_service(sid: UUID) -> None:
    global services, models
    services = [s for s in services if s.id != sid]
    models = [m for m in models if m.service_id != sid]
    _save_services()
    _save_models()


# --- model operations ---

def list_models(service_id: UUID) -> List[LLMModel]:
    return [m for m in models if m.service_id == service_id]


def create_model(data: ModelCreate) -> LLMModel:
    if not any(s.id == data.service_id for s in services):
        raise KeyError("service not found")
    for m in models:
        if m.service_id == data.service_id and m.name == data.name:
            raise ValueError("model name must be unique within service")
    mdl = LLMModel(
        id=uuid4(),
        service_id=data.service_id,
        name=data.name,
        modality=data.modality,
        context_window=data.context_window,
        supports_tools=data.supports_tools,
        extra=data.extra or {},
        created_at=datetime.utcnow(),
    )
    models.append(mdl)
    _save_models()
    return mdl


def update_model(mid: UUID, patch: ModelUpdate) -> LLMModel:
    for m in models:
        if m.id == mid:
            if patch.name and any(
                other.service_id == m.service_id and other.name == patch.name and other.id != mid
                for other in models
            ):
                raise ValueError("model name must be unique within service")
            update = m.model_copy(update=patch.model_dump(exclude_unset=True))
            models[models.index(m)] = update
            _save_models()
            return update
    raise KeyError("model not found")


def delete_model(mid: UUID) -> None:
    global models
    models = [m for m in models if m.id != mid]
    _save_models()


# --- selection ---

def get_selection(user_id: str) -> LLMSelection:
    sel = selections.get(user_id)
    if sel:
        return sel
    return LLMSelection(user_id=user_id)


def set_selection(sel: LLMSelection) -> LLMSelection:
    selections[sel.user_id] = sel
    _save_selection()
    return sel
