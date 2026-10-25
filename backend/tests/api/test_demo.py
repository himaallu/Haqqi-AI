"""POST /v1/demo/ask with a scripted LLM and a fixed law search (no database)."""

import logging

import pytest
from fastapi.testclient import TestClient

from haqqi.agents.ask import AskReply
from haqqi.api import cases, demo
from haqqi.api.main import create_app
from tests.agents.fakes import FakeLLM
from tests.agents.test_ask import LAW, PASSPORT, answer


def client_with(llm: FakeLLM) -> TestClient:
    app = create_app()
    app.dependency_overrides[cases.get_llm] = lambda: llm
    app.dependency_overrides[demo.get_search] = lambda: lambda _text: LAW
    return TestClient(app)


def test_ask_returns_the_answer_with_official_text_and_mohre_contacts(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    question = "Can my company keep my passport? My number is +971 50 123 4567"
    client = client_with(FakeLLM({"ask": [answer()]}))

    resp = client.post("/v1/demo/ask", json={"language": "en", "question": question})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kind"] == "answer"
    (cited,) = body["citations"]
    assert cited["ref_en"] == "Art. 13(2), Federal Decree-Law No. 33 of 2021"
    assert cited["text_ar"] == PASSPORT.text_ar  # quotes come from our law data, not the model
    assert [c["number"] for c in body["contacts"]] == ["80084", "600590000"]
    assert "passport" not in caplog.text and "4567" not in caplog.text


def test_safety_puts_emergency_numbers_first() -> None:
    client = client_with(FakeLLM({"ask": [answer(safety=True)]}))

    body = client.post("/v1/demo/ask", json={"language": "ur", "question": "مدد"}).json()

    assert [c["number"] for c in body["contacts"]][:2] == ["999", "8007283"]


def test_unsure_still_returns_contacts() -> None:
    client = client_with(FakeLLM({"ask": [AskReply(kind="unsure")]}))

    body = client.post("/v1/demo/ask", json={"language": "hi", "question": "?"}).json()

    assert body["kind"] == "unsure" and body["citations"] == []
    assert "80084" in [c["number"] for c in body["contacts"]]


@pytest.mark.parametrize(
    "payload",
    [
        {"language": "en", "question": ""},
        {"language": "en", "question": "x" * 1001},
        {"language": "fr", "question": "hello"},
        {"language": "en", "question": "hello", "extra": 1},
    ],
)
def test_bad_requests_get_422(payload: dict[str, object]) -> None:
    client = client_with(FakeLLM({}))

    assert client.post("/v1/demo/ask", json=payload).status_code == 422


def test_cors_regex_admits_the_demo_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    from haqqi.config import get_settings

    monkeypatch.setenv("CORS_ORIGIN_REGEX", r"https://[a-z0-9-]+\.lovable\.app")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        ok = client.options(
            "/v1/demo/ask",
            headers={
                "Origin": "https://haqqi-demo.lovable.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        other = client.options(
            "/v1/demo/ask",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
    finally:
        get_settings.cache_clear()

    assert ok.headers.get("access-control-allow-origin") == "https://haqqi-demo.lovable.app"
    assert "access-control-allow-origin" not in other.headers
