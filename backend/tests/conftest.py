import os
from urllib.parse import urlparse

import pytest

LOCAL_HOSTS = {"localhost", "127.0.0.1", "db"}
# A separate database: live tests rebuild law_chunks with the test embedder, which would wipe the
# real index that `make dev` and `make eval` use in the `haqqi` database.
DEFAULT_TEST_DB = "postgresql://haqqi:haqqi@localhost:5432/haqqi_test"


def local_test_db_url() -> str:
    """Database for live tests. They rebuild law_chunks, so they must never touch the deployed DB.

    Reads TEST_DATABASE_URL (not DATABASE_URL, which may point at Supabase) and refuses
    anything but a local host.
    """
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DB)
    host = urlparse(url).hostname
    if host not in LOCAL_HOSTS:
        raise ValueError(f"TEST_DATABASE_URL must point at a local database, not {host!r}")
    return url


@pytest.fixture
def local_db_url() -> str:
    return local_test_db_url()


def ensure_test_database() -> None:
    """Create the live-test database if it is missing (`make test-live` calls this)."""
    import psycopg

    url = urlparse(local_test_db_url())
    name = url.path.lstrip("/")
    admin = url._replace(path="/postgres").geturl()
    with psycopg.connect(admin, autocommit=True) as conn:
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            conn.execute(f'CREATE DATABASE "{name}"')
