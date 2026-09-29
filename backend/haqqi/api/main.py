"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from haqqi.config import get_settings
from haqqi.db import check_db


class Health(BaseModel):
    status: Literal["ok"]
    db: Literal["ok", "down"]
    version: str


def create_app() -> FastAPI:
    settings = get_settings()
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

    return app


app = create_app()
