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

## Tests that need running services (local database, API keys). Run `make dev` first.
## They rebuild law_chunks, so they use TEST_DATABASE_URL (local only), never DATABASE_URL.
test-live:
	$(BACKEND) export TEST_DATABASE_URL=$${TEST_DATABASE_URL:-postgresql://haqqi:haqqi@localhost:5432/haqqi} && \
		DATABASE_URL=$$TEST_DATABASE_URL uv run alembic upgrade head && uv run pytest -q -m live

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
