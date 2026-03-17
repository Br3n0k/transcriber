SHELL := /usr/bin/env bash

.PHONY: install run dev lint fmt test pre-commit

install:
	python -m venv .venv
	. .venv/Scripts/activate && pip install -U pip && pip install -r requirements.txt

run:
	. .venv/Scripts/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev: run

lint:
	. .venv/Scripts/activate && flake8 app

fmt:
	. .venv/Scripts/activate && black app && isort app

test:
	. .venv/Scripts/activate && pytest

pre-commit:
	. .venv/Scripts/activate && pre-commit install && pre-commit run --all-files