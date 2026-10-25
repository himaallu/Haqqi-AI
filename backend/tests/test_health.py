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
    assert resp.json() == {"status": "ok", "db": "down", "version": "dev", "llm": []}


def test_healthz_lists_llm_providers_in_fallback_order_without_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-secret-value")
    monkeypatch.setenv("K2_API_KEY", "k2-secret-value")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash")
    get_settings.cache_clear()
    try:
        resp = TestClient(create_app()).get("/healthz")
    finally:
        get_settings.cache_clear()

    assert resp.json()["llm"] == ["gemini:gemini-3-flash-preview", "gemini:gemini-3.5-flash", "k2"]
    assert "secret" not in resp.text


def test_healthz_reports_db_down_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@127.0.0.1:1/none")
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/healthz").json()["db"] == "down"


@pytest.mark.live
def test_healthz_reports_db_ok_with_real_database(
    monkeypatch: pytest.MonkeyPatch, local_db_url: str
) -> None:
    # Needs a running local database: `make dev`, then `make test-live`.
    monkeypatch.setenv("DATABASE_URL", local_db_url)
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/healthz").json()["db"] == "ok"
