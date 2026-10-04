"""7-day auto-delete (task 8.6) on a local Postgres. Run with `make test-live`."""

import psycopg
import pytest
from psycopg.types.json import Jsonb

from haqqi.purge import purge_expired

pytestmark = pytest.mark.live


def test_purge_deletes_a_case_created_8_days_ago_and_keeps_a_new_one(local_db_url: str) -> None:
    with psycopg.connect(local_db_url) as conn:
        old, new = (
            conn.execute(
                "INSERT INTO cases (language, status, facts, created_at, expires_at)"
                " VALUES ('en', 'ready', %s, now() - %s::interval,"
                " now() - %s::interval + interval '7 days') RETURNING id",
                (Jsonb({}), age, age),
            ).fetchone()[0]  # type: ignore[index]
            for age in ("8 days", "1 hour")
        )
        conn.commit()

        purge_expired(conn)
        conn.commit()

        ids = {
            row[0] for row in conn.execute("SELECT id FROM cases WHERE id IN (%s, %s)", (old, new))
        }
        assert ids == {new}
        conn.execute("DELETE FROM cases WHERE id = %s", (new,))
