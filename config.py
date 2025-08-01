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
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L12-v2")
LOCAL_MODEL_PATH = MODEL_DIR

# === Chunking ===
DEFAULT_CHUNKING_METHOD = "graph-pagerank"
CHUNKING_METHOD_OPTIONS = ["sentences", "semantics", "graph", "paragraphs", "dynamic", "graph-pagerank"]

# === Ollama ===
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")
