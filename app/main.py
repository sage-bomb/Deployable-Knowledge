from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import BASE_DIR, UPLOAD_DIR

from app.routes.ui_routes import router as ui_router
from api.routers.chat import router as chat_router
from api.routers.search import router as search_router
from api.routers.ingest import router as ingest_router
from api.routers.settings import router as settings_router
from app.routes.api_sessions import router as sessions_router
from app.routes.api_segments import router as segments_router
from app.auth.session import setup_auth, load_settings_from_config

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/documents", StaticFiles(directory=UPLOAD_DIR), name="documents")
manager, settings = setup_auth(app, load_settings_from_config())

# Register routes
app.include_router(ui_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(sessions_router)
app.include_router(segments_router)
app.include_router(settings_router)

