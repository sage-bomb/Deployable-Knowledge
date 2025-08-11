# === Offline-friendly env ===
export CHROMA_TELEMETRY_ENABLED=false
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export HF_HUB_OFFLINE=1

# === Config (override with: make VAR=...) ===
VENV_NAME ?= venv
PYTHON    ?= python3
PIP       := $(VENV_NAME)/bin/pip
PY        := $(VENV_NAME)/bin/python
UVICORN   := $(VENV_NAME)/bin/uvicorn
APP_MODULE?= app.main:app
MODEL_ID  ?= sentence-transformers/all-MiniLM-L6-v2


.PHONY: setup venv install fetch-model verify-offline run dev embed-dir clean test seed-prompts

# ---------- ONLINE SETUP ----------
setup: export TRANSFORMERS_OFFLINE=0
setup: export HF_DATASETS_OFFLINE=0
setup: export HF_HUB_OFFLINE=0
setup: venv install fetch-model

venv:
	$(PYTHON) -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip setuptools wheel

install:
	$(PIP) install -r requirements.txt

# Cache the embedding model into config.MODEL_DIR
fetch-model:
	@echo "📥 Caching embedding model ($(MODEL_ID))..."
	@PYTHONPATH=. $(PY) -c "from core.rag.embeddings import load_embedding_model; load_embedding_model(True); print('✓ cached via embeddings')" || \
	( echo 'model_utils failed; falling back to huggingface_hub…' && \
	  PYTHONPATH=. $(PYTHON) -c "from huggingface_hub import snapshot_download; from config import MODEL_DIR as MD; snapshot_download(repo_id='$(MODEL_ID)', local_dir=str(MD), local_dir_use_symlinks=False); print('✓ cached under', MD)" )

# ---------- OFFLINE CHECK ----------
verify-offline:
	@if [ -x "$(PY)" ]; then PYBIN="$(PY)"; else echo "⚠️  $(PY) missing; falling back to $(PYTHON)"; PYBIN="$(PYTHON)"; fi; \
	PYTHONPATH=. $$PYBIN -c "from core.rag.embeddings import load_embedding_model as L; m=L(); print('offline OK:', m.get_sentence_embedding_dimension())" || \
	PYTHONPATH=. $$PYBIN -c "from sentence_transformers import SentenceTransformer; from config import MODEL_DIR as MD; SentenceTransformer(str(MD)); print('offline OK via direct local model path ✓')"

# ---------- RUN ----------
run: verify-offline
	@if [ -x "$(UVICORN)" ]; then \
	  $(UVICORN) $(APP_MODULE) --host 127.0.0.1 --port 8000; \
	else \
	  echo "❌ $(UVICORN) not found. Run 'make setup' (online) first."; \
	  exit 127; \
	fi

dev:
	$(UVICORN) $(APP_MODULE) --host 127.0.0.1 --port 8000 --reload

# ---------- OPTIONAL: batch embed without API ----------
embed-dir:
	@echo "Embedding from documents/ (override with: make embed-dir DATA_DIR=path)"
	@PYTHONPATH=. $(PY) -c "from core.rag.retriever import embed_directory; embed_directory(data_dir='$${DATA_DIR:-documents}')"

# ---------- housekeeping ----------
clean:
	rm -rf $(VENV_NAME)
	rm -rf chroma/

test:
	pytest -q

seed-prompts:
	@$(PYTHON) -c "from core.settings import list_prompt_templates as L; t=L(); assert t, 'no prompt templates found'; print('templates:', [x.id for x in t])"
