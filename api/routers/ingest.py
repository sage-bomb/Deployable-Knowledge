import os
from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from fastapi.responses import JSONResponse
from typing import List

from core.rag.retriever import db, embed_directory, embed_file
from core.rag.chunking import parse_pdf
from api.utils import sanitize_filename
from config import UPLOAD_DIR, PDF_DIR, ALLOWED_DOCUMENT_EXTENSIONS

router = APIRouter()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Persist and embed uploaded documents.

    Parameters
    ----------
    files:
        One or more files supplied via multipart upload.

    Returns
    -------
    JSONResponse
        Status information for each uploaded file.
    """
    results = []
    for file in files:
        try:
            safe_name = sanitize_filename(file.filename, ALLOWED_DOCUMENT_EXTENSIONS)
            destination = UPLOAD_DIR / safe_name
            with open(destination, "wb") as f:
                f.write(await file.read())
            embed_file(file_path=destination, source_name=safe_name, tags=["uploaded"])
            results.append({"filename": safe_name, "status": "success"})
        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "message": str(e)})
    return JSONResponse({"uploads": results})

@router.post("/remove")
async def remove_document(source: str = Form(...)):
    """Remove a document and its embeddings from the store."""
    try:
        safe_name = sanitize_filename(source)
        db.delete_by_source(safe_name)
        file_path = UPLOAD_DIR / safe_name
        if file_path.exists():
            os.remove(file_path)
        return JSONResponse({"status": "success", "message": f"{safe_name} removed."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    """Parse any PDFs in :data:`PDF_DIR` and schedule embedding."""
    pdf_dir = PDF_DIR.resolve()
    txt_dir = UPLOAD_DIR.resolve()
    for pdf_file in pdf_dir.glob("*.pdf"):
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        try:
            parsed = parse_pdf(str(pdf_file))
            if isinstance(parsed, list):
                parsed_text = "\n\n".join([p.get("text", "") for p in parsed])
            else:
                parsed_text = parsed
            txt_file.write_text(parsed_text, encoding="utf-8")
        except Exception as e:
            print(f"Failed to parse {pdf_file.name}: {e}")
    background_tasks.add_task(
        embed_directory,
        data_dir=str(txt_dir),
        clear_collection=False,
        default_tags=["auto_ingested"],
    )
    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}

@router.post("/clear_db")
async def clear_db():
    """Delete all vectors from the backing ChromaDB collection."""
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
