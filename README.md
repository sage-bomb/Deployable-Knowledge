# Deployable-Knowledge

**Offline-First RAG System for Tactical and Edge Environments**

---

## Overview

Deployable-Knowledge is an offline-capable Retrieval-Augmented Generation (RAG) system that integrates a local LLM with document search and chat-based interaction. It’s designed to support field use where network connectivity is unavailable or restricted.

---

## Features

- **Document Ingestion**: Supports PDF, plain text, and OCR-enabled ingestion.
- **Advanced Chunking**: Multiple algorithms including sentence-based, PageRank, and semantic recursive chunking.
- **Vector Store**: Efficient local embedding storage via ChromaDB.
- **Local LLM Inference**: Compatible with `mistral:7b` and similar models running on `ollama`.
- **Live Chat + Search**: Web-based UI for contextual question answering and multi-doc search.
- **Persona Editor**: Customize assistant behavior during the session.

---

## Architecture

```text
.
├── app/                               # FastAPI application
│   ├── main.py                        # App entrypoint
│   ├── routes/                        # REST route modules
│   │   ├── api_chat_search.py         # Chat and search endpoints
│   │   ├── api_file_ingest.py         # Document ingest
│   │   └── ui_routes.py               # Serves UI
│   ├── static/                        # Frontend files
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── favicon.ico
│   │   └── js/                        # Modular JavaScript
│   │       ├── chat.js
│   │       ├── documents.js
│   │       ├── dom.js
│   │       ├── main.js
│   │       ├── marked.min.js
│   │       ├── persona_editor.js
│   │       ├── render.js
│   │       ├── search.js
│   │       ├── state.js
│   │       └── upload.js
│   └── templates/
│       └── index.html
│
├── utility/                           # Backend document + embedding logic
│   ├── chunking_algs/
│   │   ├── chunker.py
│   │   ├── chunking_test_suite.py
│   │   ├── dynamic_bottom_to_top_chunking.py
│   │   ├── dynamic_top_to_bottom_chunking.py
│   │   ├── graph_pagerank_chunking.py
│   │   └── semantic_recursive_chunking.py
│   ├── db_manager.py
│   ├── embedding_and_storing.py
│   └── parsing.py
│
├── config.py                          # Central config values
├── requirements.txt                   # Python dependencies
├── makefile                           # Common dev commands
├── README.md
└── .gitignore
```

---

## Run Instructions

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the FastAPI server:

   ```bash
   make run
   ```

3. Ensure `ollama` is running and accessible.

4. *(Optional)* Set the `OLLAMA_MODEL` environment variable if you want to use a
   different chat model than the default `mistral:7b`.

5. Navigate to `http://localhost:8000` in your browser.
