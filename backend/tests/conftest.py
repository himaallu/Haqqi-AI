import os
from urllib.parse import urlparse

import pytest

LOCAL_HOSTS = {"localhost", "127.0.0.1", "db"}
DEFAULT_TEST_DB = "postgresql://haqqi:haqqi@localhost:5432/haqqi"


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
