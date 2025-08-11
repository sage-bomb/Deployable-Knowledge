# Architecture Overview

The project is organized into three layers:

1. **core/** – Headless library that owns retrieval, prompt rendering, LLM providers and the chat pipeline.  It exposes
   Pydantic models (`ChatRequest`, `ChatResponse`, etc.) and helpers to build prompts or stream responses.
2. **api/** – Thin FastAPI adapters that translate HTTP requests into core calls.  These routers handle auth, request
   validation and markdown→HTML conversion.  Streaming uses Server‑Sent Events with `meta`, `delta`, `done` and `error`
   chunks.
3. **ui/** – Browser side ES module SDK (`DKClient`) and vanilla controllers.  Controllers never call `fetch` directly;
   instead they use `DKClient` for chat, streaming and settings.

The separation allows the core library to be reused in other apps while this repo provides a full FastAPI + JS
implementation.  A minimal example of using the browser SDK:

```js
import { DKClient } from "./static/js/ui/sdk/sdk.js";
const dk = new DKClient();
const resp = await dk.chat({ message: "hello" });
```
