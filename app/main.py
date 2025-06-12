from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()

# Mount static directories
app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_class=JSONResponse)
async def handle_query(q: str = Form(...)):
    # Dummy response; real model logic goes elsewhere
    return {
        "results": [
            {"source": "docA.txt", "preview": "Content excerpt from A", "distance": 0.123},
            {"source": "docB.pdf", "preview": "Snippet from PDF doc", "distance": 0.456}
        ]
    }
