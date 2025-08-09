import os
from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from fastapi.responses import JSONResponse
from utility.parsing import parse_pdf
from utility.embedding_and_storing import db, embed_directory, embed_file
from utility.validation import sanitize_filename

from config import (
    UPLOAD_DIR,
    PDF_DIR,
    ALLOWED_DOCUMENT_EXTENSIONS,
)

router = APIRouter()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Upload files and embed them into the database.
    This endpoint accepts multiple files, saves them to the upload directory,
    and processes each file to extract text and embed it into the database.

    - **files**: List of files to upload. Each file is processed to extract text and embed it.
    - Returns a JSON response with the status of each file upload.
    """
    results = []
    for file in files:
        try:
            safe_name = sanitize_filename(file.filename, ALLOWED_DOCUMENT_EXTENSIONS)
            destination = UPLOAD_DIR / safe_name
            with open(destination, "wb") as f:
                f.write(await file.read())

            embed_file(
                file_path=destination,
                source_name=safe_name,
                tags=["uploaded"],
            )

            results.append({"filename": safe_name, "status": "success"})
        except Exception as e:
            results.append(
                {
                    "filename": file.filename,
                    "status": "error",
                    "message": str(e),
                }
            )

    return JSONResponse({"uploads": results})

@router.post("/remove")
async def remove_document(source: str = Form(...)):
    """
    Remove a document from the database and delete its file.

    - **source**: The source name of the document to remove.
    - Returns a JSON response indicating the success or failure of the operation.
    """
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
    """
    Ingest all PDF files from the PDF_DIR, parse them, and embed the text into the database.
    This endpoint processes all PDF files in the PDF_DIR, converts them to text,
    and schedules the embedding of the text into the database.

    - **background_tasks**: FastAPI's background tasks to handle the embedding process asynchronously.
    - Returns a JSON response indicating the status of the ingestion process.
    """
    pdf_dir = PDF_DIR.resolve()
    txt_dir = UPLOAD_DIR.resolve()
    # api_file_ingest.py (inside ingest_documents)
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
        default_tags=["auto_ingested"]
    )
    return {"status": "started", "message": "Parsed PDFs and scheduled ingestion."}


@router.post("/clear_db")
async def clear_db():
    """
    Clear the ChromaDB collection.
    This endpoint removes all documents from the ChromaDB collection.
    
    - Returns a JSON response indicating the success or failure of the operation.
    """
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
