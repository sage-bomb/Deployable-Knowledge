# UI Modules

This directory hosts the browser side UI for the application.  Modules are kept small and focused so they can be recombined easily.

## Module roles
- **api.js** – wrapper around all `fetch` calls.  Each function returns parsed JSON or streaming primitives.
- **render.js** – helper functions for turning chat history or markdown into DOM nodes.
- **store.js** – centralized state; tracks the current `sessionId`, active persona text and which documents are inactive.
- **windows.js** – declares the default window layout used on start up.
- **controllers/** – feature controllers that listen for UI events and call the API:
  - `chat.js` – send messages and stream responses.
  - `docs.js` – manage the document library and upload/remove actions.
  - `sessions.js` – load session history when the user selects a past chat.
  - `search.js` – semantic document search window.
  - `persona.js` – modal for editing the assistant persona.

## Event bus
Reusable list components in `components.js` expose an `EventTarget` named `bus`.  Controllers subscribe to two custom events:

| Event name | `detail` payload |
|------------|-----------------|
| `ui:list-action` | `{ winId, elementId, action, item }` |
| `ui:list-select` | `{ winId, elementId, item, index }` |

`winId` identifies the source window and `elementId` is the component id inside that window.

## Expected API responses
`api.js` expects the backend to return the following JSON structures:

- `GET /session` or `POST /session` → `{ session_id }`
- `GET /sessions` → `[{ session_id, title, created_at }]`
- `GET /sessions/{id}` → `{ session_id, created_at, summary, title, history: [[user, assistant], ...] }`
- `GET /documents` → `[{ title, id, segments }]`
- `POST /upload` → `{ uploads: [{ filename, status, message? }] }`
- `POST /remove` → `{ status, message }`
- `GET /search?q&top_k` → `{ results: [{ text, source, score, page }] }`
- `POST /chat` → `{ response, context, chat_summary, chat_title }`
- `POST /chat-stream` → streaming body providing incremental assistant text (via `{ reader, decoder }` in `api.js`).

## Window configuration format
`windows.js` exports an array of window descriptors.  Each object at minimum contains:

```js
{
  id: "win_chat",            // unique element id
  window_type: "window_chat_ui", // key in `WindowTypes` (see window.js)
  title: "Assistant Chat",   // titlebar text
  col: "left" | "right"     // initial column
}
```

Additional optional keys include:

- `modal` – boolean, render as modal dialog.
- `Elements` – used by `window_generic` to describe form fields.
- type‑specific fields such as `value` in the persona window.

These configs are consumed by `createMiniWindowFromConfig` in `window.js` to build the DOM at runtime.

