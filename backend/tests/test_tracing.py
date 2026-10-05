"""Langfuse tracing (task 8.2): metadata only, never content; off without keys."""

import json
from typing import Any

import httpx
import pytest
from pydantic import BaseModel, SecretStr

from haqqi import tracing
from haqqi.config import Settings
from haqqi.llm.client import LLMClient, Message, Provider

PHONE = "+971 50 123 4567"
STORY = f"My boss Ramesh did not pay me for three months. Call me on {PHONE}."


class Reply(BaseModel):
    ok: bool


def client() -> LLMClient:
    body = {
        "choices": [{"message": {"content": '{"ok": true}'}}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 7},
    }
    http = httpx.Client(transport=httpx.MockTransport(lambda _r: httpx.Response(200, json=body)))
    provider = Provider("gemini:flash", "https://llm.test/v1", "flash-model", SecretStr("k"))
    return LLMClient([provider], http=http, sleep=lambda _s: None)


@pytest.fixture
def posted(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Send synchronously and capture each payload instead of calling Langfuse."""
    payloads: list[dict[str, Any]] = []
    monkeypatch.setattr(tracing, "_dispatch", lambda send: send())
    monkeypatch.setattr(tracing, "_post", payloads.append)
    return payloads


def spans(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = payload["resourceSpans"][0]["scopeSpans"][0]["spans"]
    return result


def attrs(span: dict[str, Any]) -> dict[str, str]:
    return {a["key"]: a["value"]["stringValue"] for a in span["attributes"]}


def with_keys(monkeypatch: pytest.MonkeyPatch, keys: bool) -> None:
    settings = Settings(
        langfuse_public_key=SecretStr("pk-lf-test") if keys else None,
        langfuse_secret_key=SecretStr("sk-lf-test") if keys else None,
    )
    monkeypatch.setattr(tracing, "get_settings", lambda: settings)


def test_a_traced_call_sends_stage_model_and_tokens_but_no_content(
    monkeypatch: pytest.MonkeyPatch, posted: list[dict[str, Any]]
) -> None:
    with_keys(monkeypatch, True)
    with tracing.trace("intake", language="en"):
        client().complete("intake", [Message("user", STORY)], Reply)

    [payload] = posted
    root, gen = spans(payload)
    assert attrs(root)["langfuse.trace.name"] == "intake"
    assert attrs(root)["langfuse.trace.metadata.language"] == "en"
    assert gen["traceId"] == root["traceId"] and gen["parentSpanId"] == root["spanId"]
    assert len(root["traceId"]) == 32 and len(gen["spanId"]) == 16
    g = attrs(gen)
    assert gen["name"] == "intake"
    assert g["langfuse.observation.type"] == "generation"
    assert g["langfuse.observation.model.name"] == "flash-model"
    assert g["langfuse.observation.status_message"] == "ok"
    assert json.loads(g["langfuse.observation.usage_details"]) == {"input": 120, "output": 7}
    text = json.dumps(payload)
    for secret in (PHONE, "Ramesh", "three months", "WORKER_DATA", '"ok": true'):
        assert secret not in text


def test_nothing_is_sent_without_keys(
    monkeypatch: pytest.MonkeyPatch, posted: list[dict[str, Any]]
) -> None:
    with_keys(monkeypatch, False)
    with tracing.trace("intake"):
        client().complete("intake", [Message("user", STORY)], Reply)
    assert posted == []


def test_calls_outside_a_trace_are_not_recorded(
    monkeypatch: pytest.MonkeyPatch, posted: list[dict[str, Any]]
) -> None:
    with_keys(monkeypatch, True)
    client().complete("intake", [Message("user", STORY)], Reply)
    assert posted == []


def test_a_langfuse_failure_never_reaches_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    with_keys(monkeypatch, True)

    def down(*_a: object, **_k: object) -> httpx.Response:
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", down)
    tracing._post({"resourceSpans": []})  # logs and returns


def test_set_enabled_turns_tracing_off(
    monkeypatch: pytest.MonkeyPatch, posted: list[dict[str, Any]]
) -> None:
    with_keys(monkeypatch, True)
    tracing.set_enabled(False)
    try:
        with tracing.trace("analysis"):
            client().complete("analyst", [Message("user", STORY)], Reply)
    finally:
        tracing.set_enabled(True)
    assert posted == []
