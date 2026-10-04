"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from haqqi.api.cases import router as cases_router
from haqqi.api.transcribe import router as transcribe_router
from haqqi.config import get_settings
from haqqi.db import check_db
from haqqi.logs import configure_logging


class Health(BaseModel):
    status: Literal["ok"]
    db: Literal["ok", "down"]
    version: str


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    app = FastAPI(title="Haqqi API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> Health:
        # Liveness stays "ok" even when the DB is down, so the host doesn't restart-loop us.
        db_ok = check_db(get_settings().database_url)
        return Health(status="ok", db="ok" if db_ok else "down", version=settings.git_sha)

    app.include_router(cases_router)
    app.include_router(transcribe_router)
    return app


app = create_app()
