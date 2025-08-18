from fastapi import APIRouter, Request, HTTPException, Query
from typing import List
from uuid import UUID

from app.core.llm import provider
from app.core.llm.schemas import (
    LLMService,
    ServiceCreate,
    ServiceUpdate,
    LLMModel,
    ModelCreate,
    ModelUpdate,
    LLMSelection,
)

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/services", response_model=List[LLMService])
def get_services():
    """Return all configured LLM services."""
    return provider.list_services()


@router.post("/services", response_model=LLMService, status_code=201)
def post_service(payload: ServiceCreate):
    """Register a new LLM service."""
    try:
        return provider.create_service(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/services/{sid}", response_model=LLMService)
def put_service(sid: UUID, payload: ServiceUpdate):
    """Update an existing LLM service."""
    try:
        return provider.update_service(sid, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="service not found")


@router.delete("/services/{sid}")
def del_service(sid: UUID):
    """Remove a service and any associated models."""
    provider.delete_service(sid)
    return {"ok": True}


@router.get("/models", response_model=List[LLMModel])
def get_models(service_id: UUID = Query(...)):
    """Return models for ``service_id``."""
    return provider.list_models(service_id)


@router.post("/models", response_model=LLMModel, status_code=201)
def post_model(payload: ModelCreate):
    """Create a new model entry."""
    try:
        return provider.create_model(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="service not found")


@router.put("/models/{mid}", response_model=LLMModel)
def put_model(mid: UUID, payload: ModelUpdate):
    """Update an existing model."""
    try:
        return provider.update_model(mid, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError:
        raise HTTPException(status_code=404, detail="model not found")


@router.delete("/models/{mid}")
def del_model(mid: UUID):
    """Delete a model entry."""
    provider.delete_model(mid)
    return {"ok": True}


@router.get("/selection", response_model=LLMSelection)
def get_selection(request: Request):
    """Return the user's current LLM selection."""
    user_id = getattr(request.state, "user_id", "local-user")
    return provider.get_selection(user_id)


@router.put("/selection", response_model=LLMSelection)
def put_selection(payload: LLMSelection, request: Request):
    """Persist the user's preferred service/model."""
    user_id = getattr(request.state, "user_id", "local-user")
    # Always associate selection with the requesting user
    payload.user_id = user_id
    return provider.set_selection(payload)
