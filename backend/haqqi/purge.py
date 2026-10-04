"""Delete expired cases (task 8.6, flag 21): `python -m haqqi.purge`.

Cases expire 7 days after they are created (`cases.expires_at`), and the API already refuses
expired ones. On Supabase, migration 0002 schedules the same DELETE hourly with pg_cron inside
Postgres, so it runs even while the free backend sleeps. This module is the manual equivalent,
used by tests and for databases without pg_cron.
"""

import psycopg

from haqqi.config import get_settings

PURGE_SQL = "DELETE FROM cases WHERE expires_at <= now()"


def purge_expired(conn: psycopg.Connection) -> int:
    """Delete every expired case. Returns how many were deleted."""
    return conn.execute(PURGE_SQL).rowcount


def main() -> None:
    url = get_settings().database_url
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    with psycopg.connect(url) as conn:
        print(f"deleted {purge_expired(conn)} expired cases")


if __name__ == "__main__":
    main()
