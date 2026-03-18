.PHONY: help dev test lint format format-check typecheck migrate migration \
        docker-up docker-down docker-build docker-logs docker-restart \
        venv install clean check-env

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

# Paths / config
PROJECT_ROOT := $(CURDIR)
VENV := .wslvenv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

HOST := 0.0.0.0
PORT := 8000
APP := backend.src.main:app
TESTS := ./backend/tests
BACKEND_DIR := backend

# Internal helpers
check-env:
	@if [ ! -x "$(PYTHON)" ]; then \
		echo ""; \
		echo "Virtual environment not found: $(PYTHON)"; \
		echo "Run:"; \
		echo "  make wslvenv"; \
		echo "  make install"; \
		echo ""; \
		exit 1; \
	fi

help:
	@echo "Available targets:"
	@echo "  make venv          - create .wslvenv"
	@echo "  make install       - install dependencies into .wslvenv"
	@echo "  make dev           - run FastAPI in reload mode"
	@echo "  make test          - run tests"
	@echo "  make lint          - run ruff + mypy"
	@echo "  make format        - auto-fix and format code"
	@echo "  make format-check  - check formatting only"
	@echo "  make typecheck     - run mypy only"
	@echo "  make migrate       - alembic upgrade head"
	@echo "  make migration     - create new alembic revision"
	@echo "  make docker-up     - start docker services"
	@echo "  make docker-down   - stop docker services"
	@echo "  make docker-build  - build docker services"
	@echo "  make docker-logs   - follow app logs"
	@echo "  make docker-restart- rebuild and restart services"
	@echo "  make clean         - remove caches"

# Python environment
venv:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip setuptools wheel

install: check-env
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "requirements.txt not found"; \
		exit 1; \
	fi

# Local development
dev: check-env
	$(PYTHON) -m uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

test: check-env
	$(PYTHON) -m pytest $(TESTS) -v

lint: check-env
	$(PYTHON) -m ruff check $(BACKEND_DIR)/
	$(PYTHON) -m mypy $(BACKEND_DIR)/ --ignore-missing-imports

typecheck: check-env
	$(PYTHON) -m mypy $(BACKEND_DIR)/ --ignore-missing-imports

format: check-env
	$(PYTHON) -m ruff check $(BACKEND_DIR)/ --fix
	$(PYTHON) -m ruff format $(BACKEND_DIR)/

format-check: check-env
	$(PYTHON) -m ruff format $(BACKEND_DIR)/ --check
	$(PYTHON) -m ruff check $(BACKEND_DIR)/

# Database
migrate: check-env
	$(PYTHON) -m alembic upgrade head

migration: check-env
	@read -rp "Migration message: " msg; \
	$(PYTHON) -m alembic revision --autogenerate -m "$$msg"

# Docker
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f app

docker-restart:
	docker compose down
	docker compose up -d --build

# Cleanup
clean:
	find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
