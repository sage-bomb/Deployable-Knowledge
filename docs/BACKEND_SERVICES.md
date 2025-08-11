# Backend Services Overview

The backend is composed of:

- **core/** – retrieval utilities, prompt rendering and LLM abstractions
- **api/** – FastAPI routers wrapping the core library
- **app/** – UI routes, authentication and static assets

Requests flow from the UI to `api/` where they are validated and passed to `core/` functions.  The core interacts with ChromaDB and the configured LLM provider.

Return to [docs](README.md).
