# UI Overview

The web UI served from `/` provides:

- **Chat panel** – interactive conversation with streaming updates.
- **Search bar** – perform document searches in a modal.
- **Documents view** – list of uploaded sources with segment counts.
- **Persona editor** – adjust assistant behaviour per session.

JavaScript modules under `app/static/js/` implement these features and communicate with the API via the `DKClient` SDK.

Return to [docs](README.md).
