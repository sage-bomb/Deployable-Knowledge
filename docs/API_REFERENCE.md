# API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Single chat turn; form fields `message`, `session_id`, optional `persona`, `template_id`, `top_k`, `stream` |
| `/chat-stream` | POST | Same as `/chat` but always streams Server Sent Events |
| `/search` | GET | Query documents with `q` and optional `top_k` |
| `/upload` | POST | Multipart upload of one or more documents |
| `/remove` | POST | Remove an uploaded document by filename |
| `/ingest` | POST | Parse PDFs and schedule background embedding |
| `/clear_db` | POST | Delete all vectors from ChromaDB |
| `/sessions` | GET | List stored chat sessions |
| `/sessions/{id}` | GET | Retrieve a session's history |
| `/session` | GET/POST | Fetch or create a session cookie |
| `/segments` | GET | List stored text segments |
| `/segments/{id}` | GET/DELETE | Retrieve or delete a segment |
| `/settings/{user}` | GET/PATCH | Retrieve or partially update user settings |
| `/prompt-templates` | GET/PUT | List or create prompt templates |

All endpoints return JSON except `/chat-stream`, which emits `meta`, `delta` and `done` events.

Return to [docs](README.md).
