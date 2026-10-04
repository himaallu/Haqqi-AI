.PHONY: dev down test test-live db lint format eval eval-offline eval-validate pdf-smoke

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
	$(BACKEND) uv run ruff check . ../eval && uv run ruff format --check . ../eval && uv run mypy haqqi tests
	$(BACKEND) PYTHONPATH=.. uv run mypy ../eval
	$(FRONTEND) pnpm lint && pnpm typecheck

format:
	$(BACKEND) uv run ruff check --fix . ../eval && uv run ruff format . ../eval

## Render a fixed Arabic paragraph in the backend image → out/smoke.pdf (task 5.1); open it and look
pdf-smoke:
	docker compose build backend
	mkdir -p out
	docker run --rm --user "$$(id -u):$$(id -g)" -v "$$PWD/out:/out" haqqi-backend:dev python -m haqqi.pdf.smoke /out/smoke.pdf

## Check eval/cases.jsonl: valid rows, real clause ids, hand-worked totals (tasks 7.1–7.2)
eval-validate:
	$(BACKEND) PYTHONPATH=.. uv run python -m eval.validate

## Full evaluation over eval/cases.jsonl on a local database with the law index (task 7.3).
## K2 by default (EVAL_ARGS="--provider gemini" for the free Gemini chain); resumable.
eval:
	$(BACKEND) PYTHONPATH=.. uv run python -m eval.run_eval $(EVAL_ARGS)

## No-LLM subset (task 7.4): calculator correctness (fails below 100%) + retrieval hit@5 if a DB is up
eval-offline:
	$(BACKEND) PYTHONPATH=.. uv run python -m eval.offline
