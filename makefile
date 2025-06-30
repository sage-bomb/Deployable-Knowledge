# Makefile

# kill chroma's telemetry
export CHROMA_TELEMETRY_ENABLED=false

VENV_NAME := venv
PYTHON := python3
PIP := $(VENV_NAME)/bin/pip
UVICORN := $(VENV_NAME)/bin/uvicorn
APP_MODULE := app.main:app

.PHONY: all venv install run clean

all: venv install

venv:
	$(PYTHON) -m venv $(VENV_NAME)

install: venv
	$(PIP) install -r requirements.txt
	. $(VENV_NAME)/bin/activate && python -m spacy download en_core_web_trf
	. $(VENV_NAME)/bin/activate && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

run: install
	CHROMA_TELEMETRY_ENABLED=false PYTHONPATH=. $(UVICORN) app.main:app --reload

clean:
	rm -rf $(VENV_NAME)
	rm -rf chroma/  # or whatever your DB directory is
	rm -rf tmp_model/
