import json

import httpx
import pytest
from pydantic import BaseModel, SecretStr

from haqqi.llm.client import (
    LLMClient,
    LLMOutputError,
    LLMUnavailable,
    Message,
    Provider,
    extract_json,
)


class Verdict(BaseModel):
    verdict: str
    score: int


def reply(content: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json={"choices": [{"message": {"content": content}}]})


def client_for(
    responses: list[httpx.Response], seen: list[dict[str, object]] | None = None
) -> tuple[LLMClient, list[float]]:
    queue = list(responses)
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(json.loads(request.content))
        return queue.pop(0)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    k2 = Provider("k2", "https://k2.test/v1", "m", SecretStr("secret-key"))
    return LLMClient([k2], http=http, sleep=sleeps.append), sleeps


ASK = [Message("system", "rules"), Message("user", "data")]


@pytest.mark.parametrize(
    "content",
    [
        '{"verdict": "pass", "score": 3}',
        'Sure!\n```json\n{"verdict": "pass", "score": 3}\n```',
        '<think>The user wants {json} ...</think>\n{"verdict": "pass", "score": 3}',
    ],
    ids=["plain", "fenced", "think-tag"],
)
def test_parses_valid_fenced_and_think_tag_replies(content: str) -> None:
    client, _ = client_for([reply(content)])
    assert client.complete("critic", ASK, Verdict) == Verdict(verdict="pass", score=3)


def test_invalid_json_gets_one_correction_retry() -> None:
    seen: list[dict[str, object]] = []
    client, _ = client_for(
        [reply('{"verdict": "pass"}'), reply('{"verdict": "pass", "score": 1}')], seen
    )

    assert client.complete("critic", ASK, Verdict).score == 1
    retry_messages = seen[1]["messages"]
    assert isinstance(retry_messages, list)
    assert retry_messages[-1]["role"] == "user"
    assert "score" in retry_messages[-1]["content"]  # names the missing field


def test_invalid_twice_raises_llm_output_error() -> None:
    client, _ = client_for([reply("no json here"), reply('{"verdict": 1}')])
    with pytest.raises(LLMOutputError, match="critic: invalid JSON after one retry"):
        client.complete("critic", ASK, Verdict)


def test_rate_limit_waits_retry_after_then_succeeds() -> None:
    limited = httpx.Response(429, headers={"retry-after": "3"}, json={})
    client, sleeps = client_for([limited, reply('{"verdict": "pass", "score": 2}')])

    assert client.complete("intake", ASK, Verdict).score == 2
    assert 3.0 in sleeps


def test_repeated_server_errors_raise_unavailable_without_leaking_the_key() -> None:
    client, _ = client_for([httpx.Response(503), httpx.Response(502)])
    with pytest.raises(LLMUnavailable) as err:
        client.complete("writer", ASK, Verdict)
    assert "secret-key" not in str(err.value)


def test_falls_back_to_the_next_provider() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if request.url.host == "k2.test":
            return httpx.Response(503)
        return reply('{"verdict": "pass", "score": 9}')

    http = httpx.Client(transport=httpx.MockTransport(handler))
    providers = [
        Provider("k2", "https://k2.test/v1", "m", SecretStr("a")),
        Provider("backup", "https://backup.test/v1", "m", SecretStr("b")),
    ]
    client = LLMClient(providers, http=http, sleep=_no_sleep)

    assert client.complete("intake", ASK, Verdict).score == 9
    assert calls == ["k2.test", "k2.test", "backup.test"]


def _no_sleep(_seconds: float) -> None:
    return None


def test_no_key_configured_is_unavailable() -> None:
    client = LLMClient([Provider("k2", "https://k2.test/v1", "m", None)])
    with pytest.raises(LLMUnavailable, match="K2_API_KEY"):
        client.complete("intake", ASK, Verdict)


def test_extract_json_rejects_text_without_an_object() -> None:
    with pytest.raises(ValueError):
        extract_json("I cannot help with that.")
