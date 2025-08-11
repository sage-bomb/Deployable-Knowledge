# Configuration Guide

Configuration values live in `config.py` and environment variables.

Key paths:

- `UPLOAD_DIR` – directory for user uploaded documents
- `PDF_DIR` – directory scanned for batch ingestion
- `MODEL_DIR` – location of the embedding model

Environment variables:

- `OLLAMA_MODEL` – model name for the Ollama backend
- `EMBEDDING_MODEL_ID` – sentence‑transformer to download/cache
- `EMBEDDINGS_DEVICE` – device string for embeddings (e.g. `cpu`)

Secrets and user preferences are stored under `users/` as JSON files.

Return to [docs](README.md).
