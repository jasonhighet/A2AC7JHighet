# Config Service — Makefile
# Requires: uv, standard Windows make (e.g. from GnuWin32 or Chocolatey)

.PHONY: install run migrate test test-cov help

help:
	@echo Usage:
	@echo   make install    Install all dependencies (runtime + dev)
	@echo   make run        Start the development server with hot-reload
	@echo   make migrate    Apply pending database migrations
	@echo   make test       Run the full test suite
	@echo   make test-cov   Run tests and print coverage report

install:
	uv sync --extra dev

run:
	uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

migrate:
	uv run python db/run_migrations.py

test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=term-missing
