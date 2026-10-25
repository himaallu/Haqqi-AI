"""The free-calls-left counter (haqqi/usage.py)."""

from datetime import UTC, datetime

import psycopg
import pytest

from haqqi.usage import UsageStore, key_id, quota_day


def test_the_quota_day_turns_at_midnight_pacific() -> None:
    # 25 Oct 2026 is still summer time in California (UTC-7).
    assert str(quota_day(datetime(2026, 10, 25, 6, 59, tzinfo=UTC))) == "2026-10-24"
    assert str(quota_day(datetime(2026, 10, 25, 7, 0, tzinfo=UTC))) == "2026-10-25"


def test_key_id_tells_keys_apart_without_revealing_them() -> None:
    assert key_id("first-key") == key_id("first-key")
    assert key_id("first-key") != key_id("second-key")
    assert "first" not in key_id("first-key") and len(key_id("first-key")) == 12


def test_an_unreachable_database_never_raises() -> None:
    store = UsageStore("postgresql://nobody@127.0.0.1:1/none")
    store.record("k", "gemini-3-flash-preview")
    assert store.today("k") is None


@pytest.mark.live
def test_counts_per_key_and_model(local_db_url: str) -> None:
    with psycopg.connect(local_db_url, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS llm_usage")
    store = UsageStore(local_db_url)
    store.record("key-a", "gemini-3-flash-preview")
    store.record("key-a", "gemini-3-flash-preview")
    store.record("key-a", "gemini-3.5-flash")
    store.record("key-b", "gemini-3-flash-preview")

    assert store.today("key-a") == {"gemini-3-flash-preview": 2, "gemini-3.5-flash": 1}
    assert store.today("key-new") == {}
