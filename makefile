# Makefile

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

run: install
	$(UVICORN) $(APP_MODULE) --reload

clean:
	rm -rf $(VENV_NAME)
