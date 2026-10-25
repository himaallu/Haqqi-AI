"""Counts Haqqi's Gemini calls per key, model and quota day, to estimate the free calls left.

Google's API doesn't report how much of the free daily quota is left; it only refuses with HTTP
429 once a model's limit is reached. So Haqqi counts its own successful calls (the demo's
presenter panel shows the estimate). It can't see calls made with the same key elsewhere, such
as eval runs from a laptop. Counts are kept per key fingerprint, so a new key starts at zero.

The table is created on first use (CREATE TABLE IF NOT EXISTS), because Render doesn't run
migrations on deploy; migration 0003 creates the same table for local databases.
"""

import hashlib
import logging
from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import psycopg

log = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS llm_usage (
    day date NOT NULL,
    key_id text NOT NULL,
    model text NOT NULL,
    calls integer NOT NULL DEFAULT 0,
    PRIMARY KEY (day, key_id, model)
)
"""


def quota_day(now: datetime | None = None) -> date:
    """Gemini's free daily quotas reset at midnight US Pacific time."""
    try:
        pacific: timezone | ZoneInfo = ZoneInfo("America/Los_Angeles")
    except ZoneInfoNotFoundError:  # no tz database in the image: standard time is close enough
        pacific = timezone(timedelta(hours=-8))
    return (now or datetime.now(UTC)).astimezone(pacific).date()


def key_id(secret: str) -> str:
    """A short fingerprint of an API key: tells keys apart without storing them."""
    return hashlib.sha256(secret.encode()).hexdigest()[:12]


class UsageStore:
    """Best effort: a database problem is logged and never fails an answer."""

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._ready = False

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._db_url, autocommit=True, connect_timeout=5)
        if not self._ready:
            conn.execute(DDL)
            self._ready = True
        return conn

    def record(self, key: str, model: str) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO llm_usage (day, key_id, model, calls) VALUES (%s, %s, %s, 1) "
                    "ON CONFLICT (day, key_id, model) DO UPDATE SET calls = llm_usage.calls + 1",
                    (quota_day(), key, model),
                )
        except psycopg.Error as exc:
            log.warning("usage: could not record a call (%s)", type(exc).__name__)

    def today(self, key: str) -> dict[str, int] | None:
        """Calls per model today for this key; None if the database can't be read."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT model, calls FROM llm_usage WHERE day = %s AND key_id = %s",
                    (quota_day(), key),
                ).fetchall()
        except psycopg.Error as exc:
            log.warning("usage: could not read counts (%s)", type(exc).__name__)
            return None
        return {str(model): int(calls) for model, calls in rows}
