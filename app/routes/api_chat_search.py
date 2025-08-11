from fastapi import APIRouter
from api.routers.chat import router as chat_router
from api.routers.search import router as search_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(search_router)
