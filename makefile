# Makefile for Deployable-Knowledge

# === Environment Variables ===
export CHROMA_TELEMETRY_ENABLED=false
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

# === Config ===
VENV_NAME := venv
PYTHON := python3
PIP := $(VENV_NAME)/bin/pip
UVICORN := $(VENV_NAME)/bin/uvicorn
APP_MODULE := app.main:app
MODEL_DIR := tmp_model
MODEL_FILE := $(MODEL_DIR)/config.json
STAMP_FILE := $(VENV_NAME)/.installed.ok

.PHONY: all venv install setup-online setup-offline run run-offline clean check-network

# === Master Setup ===
all: venv install

# === Virtual Environment ===
venv:
	$(PYTHON) -m venv $(VENV_NAME)

# === Dependency Installation ===
install: venv
	$(PIP) install -r requirements.txt && touch $(STAMP_FILE)

# === Online Setup ===
setup-online: install
        @if [ ! -f $(MODEL_FILE) ]; then \
                echo "📥 Downloading model..."; \
                mkdir -p $(MODEL_DIR); \
                . $(VENV_NAME)/bin/activate && \
                python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2').save('$(MODEL_DIR)')"; \
        else \
                echo "🗂️  Model already exists at $(MODEL_FILE). Skipping download."; \
        fi
        @. $(VENV_NAME)/bin/activate && python -m spacy download en_core_web_sm

# === Offline Setup ===
setup-offline: install
        @if [ ! -f $(MODEL_FILE) ]; then \
                echo "⚠️  Model not found in $(MODEL_DIR). Please run make setup-online first."; \
                exit 1; \
        else \
                echo "✅ Using existing model in $(MODEL_DIR)."; \
        fi

# === Run Logic ===
run:
	@if ping -c 1 -W 1 1.1.1.1 >/dev/null 2>&1; then \
		echo "🌐 Network detected."; \
		NEEDS_SETUP=0; \
		if [ ! -f $(STAMP_FILE) ]; then \
			echo "📦 Missing Python dependencies."; NEEDS_SETUP=1; \
		fi; \
		if [ ! -f $(MODEL_FILE) ]; then \
			echo "📁 Missing model files."; NEEDS_SETUP=1; \
		fi; \
		if [ $$NEEDS_SETUP -eq 1 ]; then \
			echo "⚙️  Running full setup..."; \
			$(MAKE) setup-online; \
		else \
			echo "✅ All requirements and model found. Skipping setup."; \
		fi; \
	else \
		echo "🚫 No network. Running in offline mode..."; \
	fi; \
	$(MAKE) run-offline

# === Run Without Setup ===
run-offline:
	PYTHONPATH=. $(UVICORN) $(APP_MODULE) --reload

# === Cleanup ===
clean:
	rm -rf $(VENV_NAME)
	rm -rf chroma/
	rm -rf $(MODEL_DIR)

