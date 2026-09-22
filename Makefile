# Convenience wrappers. See README.md / CONTRIBUTING.md for the full story.

# A virtualenv does not have the same shape everywhere: POSIX puts the entry
# points in `bin/`, Windows in `Scripts/`. Detect it instead of assuming, so a
# Windows checkout driven from Git Bash or WSL can use these targets too.
# Before `make setup` there is no venv to look at, and `bin` is the right guess
# — setup is what creates it. Likewise `python3` is the POSIX spelling; the
# python.org installer for Windows only ships `python`.
VENV := $(if $(wildcard backend/.venv/Scripts/python.exe),.venv/Scripts,.venv/bin)
PYTHON := $(if $(shell command -v python3 2>/dev/null),python3,python)
.PHONY: help up down logs update doctor \
        setup dev data dev-backend dev-frontend test lint fmt check check-backend check-frontend \
        coverage coverage-backend coverage-frontend e2e changelog

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## ── run it (Docker) ──────────────────────────────────────────────────────────

up: ## Start the app in Docker (builds from this checkout; cached, so fast)
	docker compose up -d
	@echo "→ http://localhost:$${PORT:-8080}"

down: ## Stop the Docker app
	docker compose down

logs: ## Follow the Docker app logs
	docker compose logs -f

update: ## Pull the latest code, rebuild and restart
	git pull --ff-only
	docker compose up -d --build

doctor: ## Check the toolchain / data / ports before first run
	@bash scripts/doctor.sh

## ── develop it (no Docker) ───────────────────────────────────────────────────

setup: ## Install backend + frontend dependencies
	cd backend && $(PYTHON) -m venv .venv && ../scripts/retry.sh ./$(VENV)/pip install -r requirements-dev.txt
	cd frontend && ../scripts/retry.sh npm install --ignore-scripts

data: ## Download Chummer game data into backend/vendor (gitignored)
	cd backend && ./$(VENV)/python scripts/fetch_chummer_data.py

dev: ## Run the API (:8000) and the Next dev server (:3000) together
	@bash scripts/dev.sh

dev-backend: ## Run the API with autoreload on :8000
	cd backend && ./$(VENV)/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Run the Next.js dev server on :3000
	cd frontend && npm run dev

## ── checks ──────────────────────────────────────────────────────────────────

test: ## Run the backend test suite
	cd backend && ./$(VENV)/python -m pytest -q -n auto

lint: ## Lint backend (ruff) and frontend (eslint)
	cd backend && ./$(VENV)/ruff check .
	cd frontend && npm run lint

fmt: ## Auto-format backend (ruff) and frontend (prettier)
	cd backend && ./$(VENV)/ruff format .
	cd frontend && npm run format

check-backend: ## ruff + format check + pytest + mypy
	cd backend && ./$(VENV)/ruff check . && ./$(VENV)/ruff format --check . && ./$(VENV)/python -m pytest -q -n auto && ./$(VENV)/mypy

check-frontend: ## tsc + eslint + prettier check + vitest + build
	cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build

check: check-backend check-frontend ## Everything CI runs

reconcile: ## Import Chummer's own test saves, compare karma / nuyen left, round-trip them, and check the export against what Chummer itself wrote (needs network once)
	cd backend && ./$(VENV)/python scripts/chum5_reconcile.py --roundtrip
	cd backend && ./$(VENV)/python scripts/chum5_reconcile.py --fidelity

e2e: ## Playwright: one real browser against both halves (needs `make data`)
	cd frontend && npx playwright install chromium && npm run test:e2e

coverage: coverage-backend coverage-frontend ## Coverage for both (no threshold)

coverage-backend: ## pytest --cov; HTML in backend/htmlcov/
	cd backend && ./$(VENV)/python -m pytest -q --cov --cov-report=term --cov-report=html

coverage-frontend: ## vitest --coverage; HTML in frontend/coverage/
	cd frontend && npm run test:coverage

changelog: ## Fold changelog.d/ fragments into CHANGELOG.md [Unreleased]
	$(PYTHON) scripts/changelog.py collect

release-check: ## Dry-run the release gate for VERSION=x.y.z (CHANGELOG + version bumps)
	@test -n "$(VERSION)" || { echo "usage: make release-check VERSION=0.2.0"; exit 2; }
	$(PYTHON) scripts/changelog.py check-empty
	$(PYTHON) scripts/release_notes.py $(VERSION) --check
	@echo 'ok — now: git tag -a v$(VERSION) -m v$(VERSION) && git push origin v$(VERSION)' 
