# Deployable-Knowledge

On edge/Offline knowledge retrieval and generation tool

---

## Overview

This project is a RAG (Retrieval-Augmented Generation) system that works offline with a local LLM (Large Language Model). The pipeline has these key components:

- **Document Ingestion**: Chunking and embedding uploaded source documents.
- **Vector Store**: ChromaDB is used to store and retrieve document embeddings by similarity.
- **LLM Generation**: Mistral 7b is used for generating responses based on retrieved documents.
- **API Layer**: FastAPI interface for querying and ingesting documents.

---

## Architecture

- **Embedding Model**: Can vary, an example is `all-MiniLM-L6-v2`.
- **LLM Model**: `Mistral 7b` is used for text generation.
- **Chunking Strategy**: default set to GraphRank, but other strategies such as sentence can be used.
- **Vector Store**: `ChromaDB` with persisted disk storage.

---

```text
.
├── app/                               # FastAPI app logic and route definitions
│   ├── main.py                        # Entry point for the API
│   ├── routes/                        # Modular route handlers
│   │   ├── api_file_ingest.py        # Document ingestion endpoints
│   │   ├── api_chat_search.py        # Chat and search endpoints
│   │   └── ui_routes.py              # UI-related routes
│   ├── static/                       # Static files for the FastAPI app
│   │   ├── css/
│   │   │   └── style.css             # CSS stylesheets
│   │   └── js/
│   │       └── main.js               # JavaScript files
│   └── templates/                    # HTML templates for the FastAPI app
│       └── index.html
│
├── utility/                           # Document ingestion, embedding, and indexing scripts
│   ├── chunking_algs/                # Chunking algorithms for document processing
│   │   ├── chunker.py
│   │   ├── chunking_test_suite.py
│   │   ├── dynamic_bottom_to_top_chunking.py
│   │   ├── dynamic_top_to_bottom_chunking.py
│   │   ├── graph_pagerank_chunking.py
│   │   └── semantic_recursive_chunking.py
│   ├── db_manager.py                 # ChromaDB management functions
│   ├── embedding_and_storing.py      # Embedding and storing documents
│   └── parsing.py                    # Document parsing utilities
│
├── config.py                         # Centralized configuration and environment loading
├── Makefile                          # Workflow automation: setup, run, clean
├── requirements.txt                  # Python package dependencies
├── README.md                         # Project documentation (you are here)
└── .gitignore                        # Git ignore rules
```
