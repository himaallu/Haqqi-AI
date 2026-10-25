"""POST /v1/demo/ask with a scripted LLM and a fixed law search (no database)."""

import logging

import pytest
from fastapi.testclient import TestClient

from haqqi.agents.ask import AskReply
from haqqi.api import cases, demo
from haqqi.api.main import create_app
from haqqi.llm.client import LLMClient, LLMUnavailable
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


class QuotaLLM:
    def complete(self, stage: str, messages: object, schema: object) -> object:
        raise LLMUnavailable("ask: every provider is over its quota", quota=True)


def test_quota_used_up_is_a_503_the_demo_can_recognise() -> None:
    app = create_app()
    app.dependency_overrides[cases.get_llm] = lambda: QuotaLLM()
    app.dependency_overrides[demo.get_search] = lambda: lambda _text: LAW

    resp = TestClient(app).post("/v1/demo/ask", json={"language": "en", "question": "passport?"})

    assert resp.status_code == 503
    assert "quota" in resp.json()["detail"]


def test_the_demo_header_selects_the_gemini_only_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from haqqi.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("K2_API_KEY", "k")
    get_settings.cache_clear()
    cases.demo_llm.cache_clear()
    cases._main_llm.cache_clear()
    try:
        demo_client = cases.get_llm("1")
        main_client = cases.get_llm(None)
        live = TestClient(create_app()).get("/v1/demo/status").json()
    finally:
        get_settings.cache_clear()
        cases.demo_llm.cache_clear()
        cases._main_llm.cache_clear()

    assert demo_client is not main_client
    assert isinstance(demo_client, LLMClient) and isinstance(main_client, LLMClient)
    assert [p.name for p in demo_client._providers if p.name == "k2"] == []
    assert "k2" in [p.name for p in main_client._providers]
    assert live["live"] is True


def test_status_is_not_live_without_a_gemini_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from haqqi.config import get_settings

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    get_settings.cache_clear()
    cases.demo_llm.cache_clear()
    try:
        live = TestClient(create_app()).get("/v1/demo/status").json()
    finally:
        get_settings.cache_clear()
        cases.demo_llm.cache_clear()

    assert live["live"] is False
    assert live["models"] == [] and live["calls_left"] is None


class FakeStore:
    def __init__(self, counts: dict[str, int] | None) -> None:
        self.counts = counts
        self.keys: list[str] = []

    def today(self, key: str) -> dict[str, int] | None:
        self.keys.append(key)
        return self.counts


def test_status_estimates_the_free_calls_left_for_this_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from haqqi.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "a-new-gemini-key")
    get_settings.cache_clear()
    cases.demo_llm.cache_clear()
    store = FakeStore({"gemini-3-flash-preview": 15, "gemini-3.5-flash": 25})
    monkeypatch.setattr(demo, "usage_store", lambda: store)
    try:
        client = cases.demo_llm()
        # Google refused this one for its daily quota.
        client._parked_until["gemini:gemini-3.8-flash"] = float("inf")
        body = TestClient(create_app()).get("/v1/demo/status").json()
    finally:
        get_settings.cache_clear()
        cases.demo_llm.cache_clear()

    used = {m["model"]: (m["used"], m["parked"]) for m in body["models"]}
    assert used == {
        "gemini-3-flash-preview": (15, False),
        "gemini-3.5-flash": (25, False),
        "gemini-3.8-flash": (0, True),
        "gemini-3.1-flash-lite": (0, False),
    }
    # 5 left + 0 (over its limit) + 0 (parked) + 20 untouched
    assert (body["calls_left"], body["calls_limit"]) == (25, 80)
    assert store.keys and "a-new-gemini-key" not in store.keys[0]  # a fingerprint, not the key
    assert "a-new-gemini-key" not in str(body)


def test_status_without_readable_counts_gives_no_estimate(monkeypatch: pytest.MonkeyPatch) -> None:
    from haqqi.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "g")
    get_settings.cache_clear()
    cases.demo_llm.cache_clear()
    monkeypatch.setattr(demo, "usage_store", lambda: FakeStore(None))
    try:
        body = TestClient(create_app()).get("/v1/demo/status").json()
    finally:
        get_settings.cache_clear()
        cases.demo_llm.cache_clear()

    assert body["live"] is True and body["calls_left"] is None
