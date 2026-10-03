"""One-call smoke test for each configured LLM provider.

Usage: `uv run python -m haqqi.llm.smoke`.
Prints status, latency and rate-limit headers. Never prints keys.
"""

import sys
import time
from dataclasses import dataclass, field

import httpx

from haqqi.config import Settings, get_settings
from haqqi.llm.client import Provider, providers_from_settings


@dataclass
class SmokeResult:
    provider: str
    ok: bool
    detail: str
    latency_s: float | None = None
    rate_limits: dict[str, str] = field(default_factory=dict)


def providers(settings: Settings) -> list[Provider]:
    return [
        *providers_from_settings(settings),
        Provider("groq", settings.groq_base_url, settings.groq_model, settings.groq_api_key),
    ]


def _error_message(resp: httpx.Response) -> str:
    """The provider's own error text, shortened. OpenAI-style APIs put it in error.message."""
    try:
        body = resp.json()
        error = body.get("error", body) if isinstance(body, dict) else body
        text = error.get("message", str(error)) if isinstance(error, dict) else str(error)
    except ValueError:
        text = resp.text
    return " ".join(str(text).split())[:200]


def smoke(provider: Provider, client: httpx.Client) -> SmokeResult:
    if provider.api_key is None or not provider.api_key.get_secret_value():
        return SmokeResult(provider.name, ok=False, detail="skipped: no API key set")

    url = f"{provider.base_url.rstrip('/')}/chat/completions"
    started = time.perf_counter()
    try:
        resp = client.post(
            url,
            headers={"Authorization": f"Bearer {provider.api_key.get_secret_value()}"},
            json={
                "model": provider.model,
                "messages": [{"role": "user", "content": "Reply with the single word: pong"}],
                "max_tokens": 200,
                **provider.extra,
            },
        )
    except httpx.HTTPError as exc:
        return SmokeResult(provider.name, ok=False, detail=f"request failed: {type(exc).__name__}")
    latency = round(time.perf_counter() - started, 2)
    rate_limits = {k: v for k, v in resp.headers.items() if "ratelimit" in k.lower()}

    if resp.status_code != 200:
        message = _error_message(resp).replace(provider.api_key.get_secret_value(), "***")
        detail = f"HTTP {resp.status_code} from {url} (model {provider.model}): {message}"
        return SmokeResult(provider.name, False, detail, latency, rate_limits)
    try:
        reply = resp.json()["choices"][0]["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError):
        return SmokeResult(provider.name, False, "unexpected response shape", latency, rate_limits)
    return SmokeResult(provider.name, True, f"reply: {reply.strip()[:60]!r}", latency, rate_limits)


def main() -> int:
    settings = get_settings()
    with httpx.Client(timeout=60) as client:
        results = [smoke(p, client) for p in providers(settings)]
    for r in results:
        latency = f"{r.latency_s}s" if r.latency_s is not None else "-"
        print(f"{r.provider:5} {'OK  ' if r.ok else 'FAIL'} {latency:>7}  {r.detail}")
        for k, v in r.rate_limits.items():
            print(f"      {k}: {v}")
    return 0 if any(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
