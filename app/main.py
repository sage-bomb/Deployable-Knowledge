from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import BASE_DIR, UPLOAD_DIR

from app.routes.ui_routes import router as ui_router
from app.routes.api_chat_search import router as chat_search_router
from app.routes.api_file_ingest import router as ingest_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/documents", StaticFiles(directory=UPLOAD_DIR), name="documents")

# Register routes
app.include_router(ui_router)
app.include_router(chat_search_router)
app.include_router(ingest_router)
