"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from haqqi.api.cases import router as cases_router
from haqqi.api.demo import router as demo_router
from haqqi.api.limits import LimitsMiddleware
from haqqi.api.transcribe import router as transcribe_router
from haqqi.config import get_settings
from haqqi.db import check_db
from haqqi.llm.client import providers_from_settings
from haqqi.logs import configure_logging


class Health(BaseModel):
    status: Literal["ok"]
    db: Literal["ok", "down"]
    version: str
    # LLM providers with a key set, in fallback order (names only, never keys): shows K2 is there.
    llm: list[str]


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title="Haqqi API", version="0.1.0")
    # Added first so it sits inside CORS: a 429/413 still carries the CORS headers.
    app.add_middleware(LimitsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> Health:
        # Liveness stays "ok" even when the DB is down, so the host doesn't restart-loop us.
        current = get_settings()
        db_ok = check_db(current.database_url)
        llm = [
            p.name
            for p in providers_from_settings(current)
            if p.api_key and p.api_key.get_secret_value()
        ]
        return Health(status="ok", db="ok" if db_ok else "down", version=settings.git_sha, llm=llm)

    app.include_router(cases_router)
    app.include_router(transcribe_router)
    app.include_router(demo_router)
    return app


app = create_app()
