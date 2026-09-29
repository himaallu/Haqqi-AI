"""Database helpers."""

import psycopg


def check_db(database_url: str | None) -> bool:
    """Return True if the database answers a trivial query within 2 seconds."""
    if not database_url:
        return False
    try:
        with psycopg.connect(database_url, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
