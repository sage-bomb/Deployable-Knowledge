from fastapi import APIRouter, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from utility.parsing import parse_pdf
from utility.embedding_and_storing import db, chunk_text, embed_directory

router = APIRouter()
UPLOAD_DIR = Path("documents")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile):
    try:
        destination = UPLOAD_DIR / file.filename
        with open(destination, "wb") as f:
            f.write(await file.read())
        text = parse_pdf(destination)
        chunked = chunk_text(text)
        segments = [chunk for chunk, _ in chunked]
        positions = [meta.get("char_range", (None, None)) for _, meta in chunked]
        db.add_segments(segments, strategy_name="web_ui", source=file.filename, tags=["uploaded"], positions=positions)
        return JSONResponse({"status": "success", "message": f"{file.filename} uploaded and embedded."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    pdf_dir = Path("pdfs").resolve()
    txt_dir = Path("documents").resolve()
    for pdf_file in pdf_dir.glob("*.pdf"):
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        try:
            parsed_text = parse_pdf(pdf_file)
            txt_file.write_text(parsed_text, encoding="utf-8")
        except Exception as e:
            print(f"Failed to parse {pdf_file.name}: {e}")
    background_tasks.add_task(embed_directory, data_dir=str(txt_dir), chunking_method="graph", clear_collection=False, default_tags=["auto_ingested"])
    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}

@router.post("/clear_db")
async def clear_db():
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
