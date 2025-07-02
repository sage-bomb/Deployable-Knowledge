import os
from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from fastapi.responses import JSONResponse
from pathlib import Path
from utility.parsing import parse_pdf
from utility.embedding_and_storing import db, chunk_text, embed_directory, embed_file

from config import UPLOAD_DIR, PDF_DIR, DEFAULT_CHUNKING_METHOD

router = APIRouter()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    results = []
    for file in files:
        try:
            destination = UPLOAD_DIR / file.filename
            with open(destination, "wb") as f:
                f.write(await file.read())

            embed_file(
                file_path=destination,
                chunking_method="graph",  # Or make this dynamic
                source_name=file.filename,
                tags=["uploaded"]
            )

            results.append({"filename": file.filename, "status": "success"})
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })

    return JSONResponse({"uploads": results})

@router.post("/remove")
async def remove_document(source: str = Form(...)):
    try:
        db.delete_by_source(source)
        file_path = UPLOAD_DIR / source
        if file_path.exists():
            os.remove(file_path)
        return JSONResponse({"status": "success", "message": f"{source} removed."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    pdf_dir = PDF_DIR.resolve()
    txt_dir = UPLOAD_DIR.resolve()
    for pdf_file in pdf_dir.glob("*.pdf"):
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        try:
            parsed_text = parse_pdf(pdf_file)
            txt_file.write_text(parsed_text, encoding="utf-8")
        except Exception as e:
            print(f"Failed to parse {pdf_file.name}: {e}")
    background_tasks.add_task(
        embed_directory,
        data_dir=str(txt_dir),
        chunking_method=DEFAULT_CHUNKING_METHOD,
        clear_collection=False,
        default_tags=["auto_ingested"]
    )
    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}


@router.post("/clear_db")
async def clear_db():
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
