.PHONY: dev down test test-live db lint format eval

BACKEND := cd backend &&
FRONTEND := cd frontend &&

## Start db, backend and frontend locally (http://localhost:3000)
dev:
	docker compose up --build --wait
	@echo "frontend http://localhost:3000 · backend http://localhost:8000/healthz"

down:
	docker compose down

## Unit tests: backend (pytest, no network) + frontend (vitest)
test:
	$(BACKEND) uv run pytest -q
	$(FRONTEND) pnpm test

## Tests that need running services (database, LLM keys). Run `make dev` first.
test-live:
	$(BACKEND) export DATABASE_URL=$${DATABASE_URL:-postgresql://haqqi:haqqi@localhost:5432/haqqi} && \
		uv run alembic upgrade head && uv run pytest -q -m live

## Apply database migrations to DATABASE_URL, then rebuild the law search index
db:
	$(BACKEND) uv run alembic upgrade head && uv run python -m haqqi.ingest

## ruff, mypy, eslint, tsc
lint:
	$(BACKEND) uv run ruff check . && uv run ruff format --check . && uv run mypy haqqi tests
	$(FRONTEND) pnpm lint && pnpm typecheck

format:
	$(BACKEND) uv run ruff check --fix . && uv run ruff format .

## Evaluation over eval/cases.jsonl (built in Sprint 7)
eval:
	@echo "make eval: not implemented yet; the evaluation runner arrives in Sprint 7."
