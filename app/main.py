# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from config import BASE_DIR, UPLOAD_DIR

from app.routes.ui_routes import router as ui_router
from api.routers.chat import router as chat_router
from api.routers.search import router as search_router
from api.routers.ingest import router as ingest_router
from api.routers.settings import router as settings_router
from api.routers.users import router as users_router
from app.routes.api_sessions import router as sessions_router
from app.routes.api_segments import router as segments_router
from app.routes.api_llm import router as llm_router
from app.auth.session import setup_auth, load_settings_from_config




app = FastAPI()

APP_STATIC = (BASE_DIR / "submodules" / "deployable-knowledge-web" / "src" / "static").resolve()
UI_STATIC  = (BASE_DIR / "submodules" / "deployable-ui" / "src" / "ui").resolve()

print(f"[static] APP_STATIC={APP_STATIC} exists={APP_STATIC.exists()}")
print(f"[static] UI_STATIC ={UI_STATIC}  exists={UI_STATIC.exists()}")

# Allow mounting even if the UI static directory is missing in development or
# test environments. `check_dir=False` prevents Starlette from raising an
# exception when the directory does not exist.
app.mount("/static/ui",  StaticFiles(directory=str(UI_STATIC), check_dir=False), name="ui_static")
app.mount("/static",    StaticFiles(directory=str(APP_STATIC), check_dir=False), name="static-app")

app.mount("/documents", StaticFiles(directory=str(UPLOAD_DIR), check_dir=False), name="documents")


manager, settings = setup_auth(app, load_settings_from_config())

# --- routers ---
app.include_router(ui_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(sessions_router)
app.include_router(segments_router)
app.include_router(settings_router)
app.include_router(llm_router)
app.include_router(users_router)
