# Convenience wrappers. See CONTRIBUTING.md for the full story.
.PHONY: help setup dev-backend dev-frontend data test lint fmt check check-backend check-frontend

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend + frontend dependencies
	cd backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

data: ## Download Chummer game data into backend/vendor (gitignored)
	cd backend && ./.venv/bin/python scripts/fetch_chummer_data.py

dev-backend: ## Run the API with autoreload on :8000
	cd backend && ./.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Run the Next.js dev server on :3000
	cd frontend && npm run dev

test: ## Run the backend test suite
	cd backend && ./.venv/bin/python -m pytest -q

lint: ## Lint backend (ruff) and frontend (eslint)
	cd backend && ./.venv/bin/ruff check .
	cd frontend && npm run lint

fmt: ## Auto-format backend (ruff) and frontend (prettier)
	cd backend && ./.venv/bin/ruff format .
	cd frontend && npm run format

check-backend: ## ruff + format check + pytest + mypy
	cd backend && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check . && ./.venv/bin/python -m pytest -q && ./.venv/bin/mypy

check-frontend: ## tsc + eslint + prettier check + vitest + build
	cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build

check: check-backend check-frontend ## Everything CI runs
