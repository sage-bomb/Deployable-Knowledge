# UI Overview

The web interface served from `/` lets you interact with the local RAG stack without writing any backend code.

## Getting Started
Open `http://localhost:8000` after launching the server. A session is created automatically and the UI is split into chat, search, document management and persona panes.

## Chat Panel
The chat panel streams model responses as you type. Messages are sent through the `DKClient` SDK:

```js
import { dkClient } from "./ui/sdk/sdk.js";
const sessionId = await dkClient.getOrCreateChatSession();
const reply = await dkClient.chat({
  message: "Summarise the uploaded notes",
  session_id: sessionId
});
console.log(reply.response);
```

Use `streamChat` for incremental updates during longer generations.

## Search Modal
Press `/` or click the search bar to open the search modal. Results are returned from the local vector store.

```js
const hits = await dkClient.search("battery storage", 3);
console.log(hits.results);
```

## Documents View
The documents panel lists every ingested source and the number of vector segments it contains.

```js
// Upload a file selected from an `<input type="file">`
await dkClient.uploadDocuments(input.files);
// Fetch all stored documents
const docs = await dkClient.listDocuments();
```

Documents can be removed via the UI or with `dkClient.removeDocument(name)`.

## Persona Editor
Each chat session can have a persona – short instructions that condition the assistant. Edit the persona text and new replies will adopt the updated tone or role.

## Example Workflow
1. Upload PDFs or markdown files.
2. Ask questions in the chat panel.
3. Use the search modal to inspect relevant passages.
4. Refine behaviour via the persona editor.

JavaScript modules under `app/static/js/` implement these features and communicate with the API via the `DKClient` SDK.

Return to [docs](README.md).
