"""Per-IP rate limits and request-size caps (task 8.4).

Plain ASGI middleware (not BaseHTTPMiddleware), so the analysis stream passes straight through.
It sits inside CORS, so a 429 or 413 still carries the CORS headers and the browser can show it.

Limits are kept in memory: the backend runs as one instance (Render free), and a restart only
resets the counters. The steps that call the LLM or speech service have tight limits, because the
free Gemini tier allows only about 12-15 full cases a day in total (flag 18).
"""

import json
import re
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from starlette.types import ASGIApp, Message, Receive, Scope, Send

MINUTE = 60.0


@dataclass(frozen=True)
class Rule:
    bucket: str
    method: str
    path: re.Pattern[str]
    limit: int
    window_s: float


CASE = r"/v1/cases/[^/]+"
RULES = [
    Rule("create", "POST", re.compile(r"/v1/cases/?"), 10, 10 * MINUTE),
    Rule("analyze", "POST", re.compile(CASE + r"/analyze"), 10, 10 * MINUTE),
    Rule("complaint", "POST", re.compile(CASE + r"/complaint"), 20, 10 * MINUTE),
    Rule("transcribe", "POST", re.compile(r"/v1/transcribe"), 20, 10 * MINUTE),
    Rule("api", "*", re.compile(r"/v1/.*"), 120, MINUTE),
]

# Request bodies: a case or complaint form is a few KB (story ≤ 8,000 characters); audio is
# capped at 3 MB by the endpoint, plus room for the multipart wrapping.
MAX_BODY = 64 * 1024
MAX_AUDIO_BODY = 3 * 1024 * 1024 + 64 * 1024


class SlidingWindow:
    """Request times per key; thread-safe because sync routes run in a thread pool."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_s: float) -> float | None:
        """Record a request. Returns None if allowed, else the seconds until a slot frees up."""
        now = self._clock()
        with self._lock:
            times = self._hits.setdefault(key, deque())
            while times and times[0] <= now - window_s:
                times.popleft()
            if len(times) >= limit:
                return times[0] + window_s - now
            times.append(now)
            if len(self._hits) > 10_000:  # forget idle keys so memory stays small
                self._forget_idle(now)
            return None

    def _forget_idle(self, now: float) -> None:
        longest = max(rule.window_s for rule in RULES)
        for key in [k for k, t in self._hits.items() if not t or t[-1] <= now - longest]:
            del self._hits[key]


def client_ip(scope: Scope) -> str:
    """The address that connected to the host's proxy: the last X-Forwarded-For entry.

    Earlier entries come from the client and can be faked. Without the header (local runs), the
    socket peer.
    """
    forwarded = _header(scope, b"x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    client = scope.get("client")
    return str(client[0]) if client else "unknown"


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return bytes(value).decode("latin-1")
    return None


class LimitsMiddleware:
    def __init__(self, app: ASGIApp, window: SlidingWindow | None = None) -> None:
        self.app = app
        self.window = window or SlidingWindow()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return
        path, method = scope["path"], scope["method"]

        cap = MAX_AUDIO_BODY if path.startswith("/v1/transcribe") else MAX_BODY
        length = _header(scope, b"content-length")
        if length is not None and length.isdigit() and int(length) > cap:
            await _reply(send, 413, {"detail": "The request is too large."})
            return
        if length is None and _header(scope, b"transfer-encoding"):
            await _reply(send, 411, {"detail": "Content-Length is required."})
            return

        ip = client_ip(scope)
        for rule in RULES:
            if rule.method in ("*", method) and rule.path.fullmatch(path):
                wait = self.window.hit(f"{rule.bucket}:{ip}", rule.limit, rule.window_s)
                if wait is not None:
                    detail = "Too many requests. Please wait a few minutes and try again."
                    await _reply(send, 429, {"detail": detail}, retry_after=wait)
                    return
        await self.app(scope, receive, send)


async def _reply(
    send: Send, status: int, body: dict[str, str], retry_after: float | None = None
) -> None:
    payload = json.dumps(body).encode()
    headers = [(b"content-type", b"application/json"), (b"content-length", b"%d" % len(payload))]
    if retry_after is not None:
        headers.append((b"retry-after", b"%d" % max(1, round(retry_after))))
    start: Message = {"type": "http.response.start", "status": status, "headers": headers}
    await send(start)
    await send({"type": "http.response.body", "body": payload})
