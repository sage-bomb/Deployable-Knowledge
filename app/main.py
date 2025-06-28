
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routes.ui_routes import router as ui_router
from app.routes.api_chat_search import router as chat_search_router
from app.routes.api_file_ingest import router as ingest_router

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Register routes
app.include_router(ui_router)
app.include_router(chat_search_router)
app.include_router(ingest_router)
