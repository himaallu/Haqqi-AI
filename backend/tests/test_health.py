import pytest
from fastapi.testclient import TestClient

from haqqi.api.main import create_app
from haqqi.config import get_settings


def test_healthz_reports_db_down_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    resp = client.get("/healthz")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "down", "version": "dev"}


def test_healthz_reports_db_down_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/healthz").json()["db"] == "down"


@pytest.mark.live
def test_healthz_reports_db_ok_with_real_database() -> None:
    # Needs a running database: `make dev`, then `make test-live`.
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/healthz").json()["db"] == "ok"
