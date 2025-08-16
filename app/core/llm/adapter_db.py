from uuid import UUID
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

# Placeholder DB-backed implementation

def list_services() -> List[LLMService]:  # pragma: no cover - stub
    raise NotImplementedError


def create_service(data: ServiceCreate) -> LLMService:  # pragma: no cover - stub
    raise NotImplementedError


def update_service(sid: UUID, patch: ServiceUpdate) -> LLMService:  # pragma: no cover - stub
    raise NotImplementedError


def delete_service(sid: UUID) -> None:  # pragma: no cover - stub
    raise NotImplementedError


def list_models(service_id: UUID) -> List[LLMModel]:  # pragma: no cover - stub
    raise NotImplementedError


def create_model(data: ModelCreate) -> LLMModel:  # pragma: no cover - stub
    raise NotImplementedError


def update_model(mid: UUID, patch: ModelUpdate) -> LLMModel:  # pragma: no cover - stub
    raise NotImplementedError


def delete_model(mid: UUID) -> None:  # pragma: no cover - stub
    raise NotImplementedError


def get_selection(user_id: str) -> LLMSelection:  # pragma: no cover - stub
    raise NotImplementedError


def set_selection(sel: LLMSelection) -> LLMSelection:  # pragma: no cover - stub
    raise NotImplementedError
