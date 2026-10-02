import pytest

from tests.conftest import DEFAULT_TEST_DB, local_test_db_url


def test_live_tests_ignore_database_url_and_default_to_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@aws-0-x.pooler.supabase.com:5432/postgres")
    assert local_test_db_url() == DEFAULT_TEST_DB


def test_live_tests_refuse_a_remote_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql://u:p@aws-0-x.pooler.supabase.com/postgres")
    with pytest.raises(ValueError, match="local database"):
        local_test_db_url()
