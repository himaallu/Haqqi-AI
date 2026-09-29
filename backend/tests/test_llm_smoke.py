import httpx
from pydantic import SecretStr

from haqqi.llm.smoke import Provider, smoke

KEY = "sk-test-secret-123"


def provider(key: str | None = KEY) -> Provider:
    return Provider("k2", "https://llm.example/v1", "m", SecretStr(key) if key else None)


def client_returning(
    status: int, body: object, headers: dict[str, str] | None = None
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        return httpx.Response(status, json=body, headers=headers)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_skips_provider_without_key() -> None:
    result = smoke(provider(key=None), httpx.Client())
    assert not result.ok
    assert result.detail.startswith("skipped")


def test_reports_reply_latency_and_rate_limits_without_leaking_key() -> None:
    body = {"choices": [{"message": {"content": "pong"}}]}
    client = client_returning(200, body, {"x-ratelimit-remaining-requests": "29"})

    result = smoke(provider(), client)

    assert result.ok
    assert "pong" in result.detail
    assert result.latency_s is not None
    assert result.rate_limits == {"x-ratelimit-remaining-requests": "29"}
    assert KEY not in repr(result)


def test_reports_http_error_status() -> None:
    result = smoke(provider(), client_returning(401, {"error": "bad key"}))
    assert not result.ok
    assert result.detail == "HTTP 401"
