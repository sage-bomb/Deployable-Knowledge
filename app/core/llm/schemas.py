from pydantic import BaseModel, Field, AnyUrl, conint, constr
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class LLMService(BaseModel):
    id: UUID
    name: str
    provider: str
    base_url: Optional[str] = None
    auth_ref: Optional[str] = None
    timeout_sec: Optional[int] = None
    is_enabled: bool = True
    extra: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class ServiceCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    provider: constr(strip_whitespace=True, min_length=1)
    base_url: Optional[AnyUrl] = None
    auth_ref: Optional[str] = None
    timeout_sec: Optional[conint(ge=1, le=600)] = None
    is_enabled: bool = True
    extra: Dict[str, Any] = Field(default_factory=dict)


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[AnyUrl] = None
    auth_ref: Optional[str] = None
    timeout_sec: Optional[conint(ge=1, le=600)] = None
    is_enabled: Optional[bool] = None
    extra: Optional[Dict[str, Any]] = None


class LLMModel(BaseModel):
    id: UUID
    service_id: UUID
    name: str
    model_name: str
    modality: Optional[str] = None
    context_window: Optional[int] = None
    supports_tools: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class ModelCreate(BaseModel):
    service_id: UUID
    name: constr(strip_whitespace=True, min_length=1)
    model_name: constr(strip_whitespace=True, min_length=1)
    modality: Optional[str] = None
    context_window: Optional[conint(ge=1, le=1048576)] = None
    supports_tools: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    model_name: Optional[str] = None
    modality: Optional[str] = None
    context_window: Optional[conint(ge=1, le=1048576)] = None
    supports_tools: Optional[bool] = None
    extra: Optional[Dict[str, Any]] = None


class LLMSelection(BaseModel):
    user_id: Optional[str] = None
    service_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
