"""OpenAI-compatible chat client for the agents (task 3.5).

Every reply is parsed into a Pydantic model (CLAUDE.md): invalid JSON gets one retry with a
short correction, then `LLMOutputError`. Transport failures get one retry, then the next
provider in the list (flag 18; K2 only in v1), then `LLMUnavailable`. Calls are serialised
and spaced to respect K2's 2 requests/second (flag 20). Logs never contain content or keys.
"""

import json
import logging
import re
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

import httpx
from pydantic import BaseModel, SecretStr, ValidationError

from haqqi.config import Settings

log = logging.getLogger(__name__)

TIMEOUT_S = 90.0  # K2 calls measured 5-77 s on 2 Oct; a shorter cap only wastes a retry
MIN_GAP_S = 0.5  # 2 requests/second
MAX_RETRY_AFTER_S = 10.0

_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"```(?:json)?")


class LLMError(Exception):
    pass


class LLMUnavailable(LLMError):
    """No provider answered (timeouts, 5xx, rate limits). Show "try again later"."""


class LLMOutputError(LLMError):
    """The model's reply did not parse into the expected schema, even after one retry."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    api_key: SecretStr | None


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


def extract_json(text: str) -> str:
    """Strip reasoning tags and code fences; keep the outermost JSON object (ports `parseK2`)."""
    text = _FENCE.sub("", _THINK.sub("", text)).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object in the reply")
    return text[start : end + 1]


def parse_reply[T: BaseModel](text: str, schema: type[T]) -> T:
    try:
        return schema.model_validate_json(extract_json(text))
    except (ValueError, ValidationError) as exc:
        raise _ParseFailure(_short_error(exc)) from exc


class _ParseFailure(Exception):
    pass


def _short_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        parts = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()[:5]]
        return "; ".join(parts)
    return str(exc)[:200]


class Completer(Protocol):
    """What agents need from a client; `LLMClient` in production, a scripted fake in tests."""

    def complete[T: BaseModel](
        self, stage: str, messages: Sequence[Message], schema: type[T]
    ) -> T: ...


class LLMClient:
    def __init__(
        self,
        providers: Sequence[Provider],
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._providers = [p for p in providers if p.api_key and p.api_key.get_secret_value()]
        self._http = http or httpx.Client(timeout=TIMEOUT_S)
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last_call = 0.0

    @classmethod
    def from_settings(cls, settings: Settings) -> "LLMClient":
        return cls([Provider("k2", settings.k2_base_url, settings.k2_model, settings.k2_api_key)])

    def complete[T: BaseModel](self, stage: str, messages: Sequence[Message], schema: type[T]) -> T:
        """Chat call parsed into `schema`; one correction retry on bad output."""
        convo = list(messages)
        reply = self._chat(stage, convo)
        try:
            return parse_reply(reply, schema)
        except _ParseFailure as first:
            log.warning("llm %s: invalid output, retrying once (%s)", stage, first)
            convo += [
                Message("assistant", reply),
                Message(
                    "user",
                    f"Your reply was not valid for the required JSON format ({first}). "
                    "Reply again with ONLY the corrected JSON object.",
                ),
            ]
            reply = self._chat(stage, convo)
            try:
                return parse_reply(reply, schema)
            except _ParseFailure as second:
                raise LLMOutputError(f"{stage}: invalid JSON after one retry ({second})") from None

    def _chat(self, stage: str, messages: Sequence[Message]) -> str:
        if not self._providers:
            raise LLMUnavailable("no LLM provider configured (K2_API_KEY is empty)")
        for provider in self._providers:
            for attempt in (1, 2):
                outcome = self._post(stage, provider, messages)
                if isinstance(outcome, str):
                    return outcome
                if attempt == 1:
                    self._sleep(outcome)
            log.warning("llm %s: provider %s unavailable", stage, provider.name)
        raise LLMUnavailable(f"{stage}: the language model is not responding, try again later")

    def _post(self, stage: str, provider: Provider, messages: Sequence[Message]) -> str | float:
        """The reply text, or how long to wait before retrying."""
        assert provider.api_key is not None
        with self._lock:
            wait = self._last_call + MIN_GAP_S - time.monotonic()
            if wait > 0:
                self._sleep(wait)
            self._last_call = time.monotonic()
        started = time.perf_counter()
        try:
            resp = self._http.post(
                f"{provider.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {provider.api_key.get_secret_value()}"},
                json={
                    "model": provider.model,
                    "messages": [m.as_dict() for m in messages],
                    "temperature": 0,
                },
                timeout=TIMEOUT_S,
            )
        except httpx.HTTPError as exc:
            log.warning("llm %s: %s %s", stage, provider.name, type(exc).__name__)
            return 1.0
        latency = time.perf_counter() - started
        if resp.status_code == 429:
            retry_after = _retry_after(resp)
            log.warning("llm %s: rate limited, waiting %.1fs", stage, retry_after)
            return retry_after
        if resp.status_code >= 500:
            log.warning("llm %s: HTTP %s", stage, resp.status_code)
            return 1.0
        if resp.status_code != 200:
            raise LLMUnavailable(f"{stage}: HTTP {resp.status_code} from {provider.name}")
        try:
            body = resp.json()
            text = body["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError):
            log.warning("llm %s: unexpected response shape", stage)
            return 1.0
        usage = body.get("usage") or {}
        log.info(
            "llm %s: ok in %.1fs, tokens in=%s out=%s",
            stage,
            latency,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return str(text)


def _retry_after(resp: httpx.Response) -> float:
    try:
        return min(float(resp.headers.get("retry-after", "2")), MAX_RETRY_AFTER_S)
    except ValueError:
        return 2.0


def dump_json(data: object) -> str:
    """Compact, stable JSON for prompts."""
    return json.dumps(data, ensure_ascii=False, indent=1, default=str)
