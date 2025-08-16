import os

from .schemas import (
    LLMService,
    ServiceCreate,
    ServiceUpdate,
    LLMModel,
    ModelCreate,
    ModelUpdate,
    LLMSelection,
)

if os.getenv("LLM_REGISTRY_MOCK", "1") == "1":
    from . import adapter_mock as adapter
else:  # pragma: no cover - DB adapter not implemented
    from . import adapter_db as adapter


list_services = adapter.list_services
create_service = adapter.create_service
update_service = adapter.update_service
delete_service = adapter.delete_service

list_models = adapter.list_models
create_model = adapter.create_model
update_model = adapter.update_model
delete_model = adapter.delete_model

get_selection = adapter.get_selection
set_selection = adapter.set_selection
