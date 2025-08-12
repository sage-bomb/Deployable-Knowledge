# Deployable-Knowledge

**Version 0.9.0**

Offline‑first retrieval‑augmented generation (RAG) stack for disconnected or bandwidth‑constrained environments.

## Overview

Deployable‑Knowledge bundles a local vector store, prompt management and a lightweight web UI around a pluggable large‑language model.  Documents are embedded locally and queried through FastAPI endpoints which power the JavaScript front end.

## Features

- **Document ingestion** for PDF and plaintext sources
- **ChromaDB** vector store with sentence‑transformer embeddings
- **Chat and search** endpoints with optional streaming responses
- **Configurable prompts** and persona editing
- **Authentication middleware** with session and CSRF protection

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make run
```

Visit <http://localhost:8000> once the server starts.  `ollama` must be running locally and can be configured via environment variables such as `OLLAMA_MODEL`.

## Architecture overview

The system is split into three layers:

```text
core/  – retrieval, prompt rendering and LLM adapters
api/   – FastAPI routers translating HTTP ↔ core
app/   – static assets and UI routes
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams and data‑flow breakdowns.

## Documentation

Additional guides live in the [`docs/`](docs) folder:

- [API reference](docs/API_REFERENCE.md)
- [UI overview](docs/UI_OVERVIEW.md)
- [Backend services](docs/BACKEND_SERVICES.md)
- [Configuration guide](docs/CONFIGURATION.md)
- [Prompt & LLM integration](docs/PROMPTS_LLM.md)

## Contributing

1. Create a feature branch off `main`.
2. Add tests and run `pytest` before submitting a pull request.
3. Follow the existing coding style and keep docstrings concise.
4. Open a PR describing the change and link to any relevant issues.

---
Released under the MIT license.
