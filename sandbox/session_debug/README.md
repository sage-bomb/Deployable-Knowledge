# Session Debug Sandbox

This directory contains a minimal, self-contained environment for experimenting
with session logic **without** involving the project's FastAPI routes, frontend
JavaScript, or NLP components. The goal is to isolate and validate session ID
handling before integrating it back into the full application.

## Contents
- `session_state.py` – simple setters/getters for a session ID.
- `session_test.py` – small test suite that exercises the session state.

## Usage
Run the tests directly with Python:

```bash
python session_test.py
```

No third‑party packages or frameworks are required for this sandbox.
