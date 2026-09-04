# Convenience wrappers. See README.md / CONTRIBUTING.md for the full story.
.PHONY: help up down logs update doctor \
        setup dev data dev-backend dev-frontend test lint fmt check check-backend check-frontend \
        coverage coverage-backend coverage-frontend e2e

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## ── run it (Docker) ──────────────────────────────────────────────────────────

up: ## Start the app in Docker (pulls the published image if available)
	-docker compose pull --quiet 2>/dev/null || true
	docker compose up -d
	@echo "→ http://localhost:$${PORT:-8080}"

down: ## Stop the Docker app
	docker compose down

logs: ## Follow the Docker app logs
	docker compose logs -f

update: ## Pull the latest code + image and restart
	git pull --ff-only
	-docker compose pull --quiet 2>/dev/null || true
	docker compose up -d --build

doctor: ## Check the toolchain / data / ports before first run
	@bash scripts/doctor.sh

## ── develop it (no Docker) ───────────────────────────────────────────────────

setup: ## Install backend + frontend dependencies
	cd backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

data: ## Download Chummer game data into backend/vendor (gitignored)
	cd backend && ./.venv/bin/python scripts/fetch_chummer_data.py

dev: ## Run the API (:8000) and the Next dev server (:3000) together
	@bash scripts/dev.sh

dev-backend: ## Run the API with autoreload on :8000
	cd backend && ./.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Run the Next.js dev server on :3000
	cd frontend && npm run dev

## ── checks ──────────────────────────────────────────────────────────────────

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

e2e: ## Playwright: one real browser against both halves (needs `make data`)
	cd frontend && npx playwright install chromium && npm run test:e2e

coverage: coverage-backend coverage-frontend ## Coverage for both (no threshold)

coverage-backend: ## pytest --cov; HTML in backend/htmlcov/
	cd backend && ./.venv/bin/python -m pytest -q --cov --cov-report=term --cov-report=html

coverage-frontend: ## vitest --coverage; HTML in frontend/coverage/
	cd frontend && npm run test:coverage

release-check: ## Dry-run the release gate for VERSION=x.y.z (CHANGELOG + version bumps)
	@test -n "$(VERSION)" || { echo "usage: make release-check VERSION=0.2.0"; exit 2; }
	python3 scripts/release_notes.py $(VERSION) --check
	@echo 'ok — now: git tag -a v$(VERSION) -m v$(VERSION) && git push origin v$(VERSION)' 
