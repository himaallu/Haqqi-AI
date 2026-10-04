"""Per-IP rate limits and request-size caps (task 8.4). No database or LLM needed."""

from fastapi.testclient import TestClient

from haqqi.api import cases
from haqqi.api.limits import MAX_BODY, SlidingWindow
from haqqi.api.main import create_app
from haqqi.config import get_settings


def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[cases.get_database_url] = lambda: "postgresql://unused"
    return TestClient(app)


def test_thirty_rapid_case_requests_get_429_after_the_limit() -> None:
    api = client()
    origin = get_settings().cors_origins[0]
    codes = [
        api.post("/v1/cases", json={}, headers={"Origin": origin}).status_code for _ in range(30)
    ]
    assert codes[:10] == [422] * 10  # reached the app (invalid body)
    assert codes[10:] == [429] * 20
    blocked = api.post("/v1/cases", json={}, headers={"Origin": origin})
    assert 0 < int(blocked.headers["retry-after"]) <= 600
    assert blocked.headers["access-control-allow-origin"] == origin  # the browser can read it
    assert "try again" in blocked.json()["detail"]


def test_limits_are_per_client_and_a_faked_forwarded_address_does_not_help() -> None:
    api = client()
    for _ in range(10):
        api.post("/v1/cases", json={}, headers={"X-Forwarded-For": "1.1.1.1"})
    # The client can prepend anything; the last entry is the one the host's proxy added.
    spoofed = api.post("/v1/cases", json={}, headers={"X-Forwarded-For": "9.9.9.9, 1.1.1.1"})
    assert spoofed.status_code == 429
    other = api.post("/v1/cases", json={}, headers={"X-Forwarded-For": "2.2.2.2"})
    assert other.status_code == 422


def test_only_the_api_routes_are_limited() -> None:
    api = client()  # /healthz and the docs sit outside /v1
    assert all(api.get("/openapi.json").status_code == 200 for _ in range(150))


def test_oversized_bodies_get_413() -> None:
    api = client()
    big = api.post(
        "/v1/cases", content=b"x" * (MAX_BODY + 1), headers={"content-type": "application/json"}
    )
    assert big.status_code == 413
    audio = api.post(
        "/v1/transcribe", files={"audio": ("a.webm", b"0" * (4 * 1024 * 1024), "audio/webm")}
    )
    assert audio.status_code == 413


def test_audio_under_the_cap_reaches_the_endpoint() -> None:
    api = client()
    small = api.post("/v1/transcribe", files={"audio": ("a.webm", b"", "audio/webm")})
    assert small.status_code not in (411, 413, 429)


def test_sliding_window_frees_slots_as_time_passes() -> None:
    now = [0.0]
    window = SlidingWindow(clock=lambda: now[0])
    assert window.hit("k", 2, 60) is None
    now[0] = 10
    assert window.hit("k", 2, 60) is None
    assert window.hit("k", 2, 60) == 50  # the first request frees its slot at t=60
    now[0] = 60
    assert window.hit("k", 2, 60) is None
