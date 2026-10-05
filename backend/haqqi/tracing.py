"""Langfuse tracing of LLM calls (task 8.2), metadata only.

Each case step (intake, analysis) is one trace. Each LLM HTTP call is one generation with the
stage, provider, model, timing, token counts and outcome. Never sent: the story, prompts,
replies, names, amounts or case ids (the trace id is a fresh random id).

Spans go to Langfuse's OpenTelemetry endpoint (OTLP over HTTP/JSON) with httpx rather than through
the Langfuse SDK, so nothing else can be captured by accident and the backend stays small (Render
free plan, 512 MB). Langfuse's older ingestion API shuts down on 16 Nov 2026 for traces; the OTel
endpoint is its replacement. One request is posted per trace from a daemon thread; the app never
waits on Langfuse, and a Langfuse failure is logged by type only. Without keys (tests, CI, local
runs) nothing is sent.
"""

import json
import logging
import secrets
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

from haqqi.config import get_settings

log = logging.getLogger(__name__)
TIMEOUT_S = 5.0


@dataclass
class _Trace:
    name: str
    metadata: dict[str, str]
    id: str = field(default_factory=lambda: secrets.token_hex(16))  # OTel trace id
    span_id: str = field(default_factory=lambda: secrets.token_hex(8))
    started: datetime = field(default_factory=lambda: datetime.now(UTC))
    generations: list[dict[str, Any]] = field(default_factory=list)


_current: ContextVar[_Trace | None] = ContextVar("haqqi_trace", default=None)
_enabled = True


def set_enabled(on: bool) -> None:
    """Turn tracing off for batch runs such as the evaluation."""
    global _enabled
    _enabled = on


def _dispatch(send: Callable[[], None]) -> None:
    threading.Thread(target=send, daemon=True).start()


@contextmanager
def trace(name: str, **metadata: str) -> Iterator[None]:
    """Group the LLM calls made inside this block into one Langfuse trace."""
    settings = get_settings()
    if not (_enabled and settings.langfuse_public_key and settings.langfuse_secret_key):
        yield
        return
    current = _Trace(name, metadata)
    token = _current.set(current)
    try:
        yield
    finally:
        _current.reset(token)
        payload = build_payload(current, datetime.now(UTC))
        _dispatch(lambda: _post(payload))


def generation(
    *,
    stage: str,
    provider: str,
    model: str,
    start: datetime,
    end: datetime,
    outcome: str,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> None:
    """Record one LLM call in the current trace (a no-op outside one)."""
    current = _current.get()
    if current is None:
        return
    current.generations.append(
        {
            "name": stage,
            "start": start,
            "end": end,
            "attributes": {
                "langfuse.observation.type": "generation",
                "langfuse.observation.model.name": model,
                "langfuse.observation.usage_details": json.dumps(
                    {"input": tokens_in or 0, "output": tokens_out or 0}
                ),
                "langfuse.observation.level": "DEFAULT" if outcome == "ok" else "WARNING",
                "langfuse.observation.status_message": outcome,
                "langfuse.observation.metadata.provider": provider,
            },
        }
    )


def _nanos(moment: datetime) -> str:
    return str(int(moment.timestamp() * 1_000_000_000))


def _attributes(values: dict[str, str]) -> list[dict[str, Any]]:
    return [{"key": k, "value": {"stringValue": v}} for k, v in values.items()]


def build_payload(current: _Trace, ended: datetime) -> dict[str, Any]:
    """The trace as OTLP JSON: one root span plus one child span per LLM call."""
    root = {
        "traceId": current.id,
        "spanId": current.span_id,
        "name": current.name,
        "kind": 1,
        "startTimeUnixNano": _nanos(current.started),
        "endTimeUnixNano": _nanos(ended),
        "attributes": _attributes(
            {
                "langfuse.trace.name": current.name,
                "langfuse.observation.type": "span",
                **{f"langfuse.trace.metadata.{k}": v for k, v in current.metadata.items()},
            }
        ),
    }
    children = [
        {
            "traceId": current.id,
            "spanId": secrets.token_hex(8),
            "parentSpanId": current.span_id,
            "name": g["name"],
            "kind": 3,
            "startTimeUnixNano": _nanos(g["start"]),
            "endTimeUnixNano": _nanos(g["end"]),
            "attributes": _attributes(g["attributes"]),
        }
        for g in current.generations
    ]
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": _attributes({"service.name": "haqqi-api"})},
                "scopeSpans": [{"scope": {"name": "haqqi"}, "spans": [root, *children]}],
            }
        ]
    }


def _post(payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return
    try:
        resp = httpx.post(
            f"{settings.langfuse_host.rstrip('/')}/api/public/otel/v1/traces",
            auth=(
                settings.langfuse_public_key.get_secret_value(),
                settings.langfuse_secret_key.get_secret_value(),
            ),
            # Version 4 makes the spans visible right away (Langfuse's v4 data model).
            headers={"x-langfuse-ingestion-version": "4"},
            json=payload,
            timeout=TIMEOUT_S,
        )
        if resp.status_code >= 300:
            log.warning("langfuse: HTTP %s", resp.status_code)
    except httpx.HTTPError as exc:
        log.warning("langfuse: %s", type(exc).__name__)
