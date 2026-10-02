"""Alembic environment: plain SQL migrations, database URL from settings."""

from alembic import context
from sqlalchemy import create_engine

from haqqi.config import get_settings


def sqlalchemy_url() -> str:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    # Use the psycopg 3 driver we already depend on.
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


def run_migrations_online() -> None:
    engine = create_engine(sqlalchemy_url())
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
