# API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Single chat turn; form fields `message`, `session_id`, optional `service_id`, `model_id`, `persona`, `template_id`, `top_k`, `stream` |
| `/chat-stream` | POST | Same as `/chat` but always streams Server Sent Events; form fields `message`, `session_id`, optional `service_id`, `model_id`, `persona`, `template_id`, `top_k` |
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
| `/api/users` | GET | List users |
| `/api/users/{id}` | GET | Retrieve a user record |
| `/prompt-templates` | GET/PUT | List or create prompt templates |

All endpoints return JSON except `/chat-stream`, which emits `meta`, `delta` and `done` events.

### Selecting a model

Both `/chat` and `/chat-stream` accept optional `service_id` and `model_id` fields. When provided, the chat pipeline will invoke the specified model for the request.

Example:

```
curl -X POST http://localhost:8000/chat \
  -F message='hi' \
  -F session_id='<session_uuid>' \
  -F service_id='<service_uuid>' \
  -F model_id='<model_uuid>'
```

Return to [docs](README.md).
