from pathlib import Path
import os

# === Base Paths ===
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "documents"
PDF_DIR = BASE_DIR / "pdfs"
MODEL_DIR = BASE_DIR / "tmp_model"

# === ChromaDB ===
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "default_collection"

# === Embedding Model ===
# Always point to a local directory for offline model loading
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", str(MODEL_DIR))

# === Security ===
ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".pdf", ".md", ".html"}
MIN_TOP_K = 1
MAX_TOP_K = 20

# === Ollama ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")
