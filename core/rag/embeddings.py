from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import os
from typing import Optional
from sentence_transformers import SentenceTransformer

try:
    from huggingface_hub import snapshot_download  # optional
except Exception:
    snapshot_download = None

from config import MODEL_DIR

EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDINGS_OFFLINE_ONLY = os.getenv("EMBEDDINGS_OFFLINE_ONLY", "0") == "1"


def _local_model_present(model_dir: Path) -> bool:
    return model_dir.exists() and any(model_dir.iterdir())


def fetch_model_if_needed(model_id: str = EMBEDDING_MODEL_ID, model_dir: Path = MODEL_DIR) -> Path:
    if _local_model_present(model_dir):
        return model_dir
    if EMBEDDINGS_OFFLINE_ONLY:
        raise RuntimeError(f"Offline-only mode set, but model not found at {model_dir}")
    if snapshot_download is None:
        raise RuntimeError("huggingface_hub not available to fetch model.")
    snapshot_download(
        repo_id=model_id,
        local_dir=str(model_dir),
        local_dir_use_symlinks=False,
        allow_patterns=None,
        ignore_patterns=["*.safetensors.index.json"],
    )
    return model_dir


@lru_cache(maxsize=1)
def load_embedding_model(force_fetch: bool = False) -> SentenceTransformer:
    model_dir = Path(MODEL_DIR)
    if force_fetch:
        fetch_model_if_needed()
    elif not _local_model_present(model_dir):
        if EMBEDDINGS_OFFLINE_ONLY:
            raise RuntimeError(f"Model cache missing at {model_dir} and offline-only is enabled.")
        fetch_model_if_needed()
    return SentenceTransformer(str(model_dir), device=os.getenv("EMBEDDINGS_DEVICE", "cpu"))
