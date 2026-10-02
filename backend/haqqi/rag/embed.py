"""Text embedders. Retrieval depends only on the `Embedder` protocol (flag 15)."""

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

import httpx

from haqqi.config import Settings


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One unit-length vector per text."""
        ...


class HashEmbedder:
    """Deterministic stand-in for tests and offline development.

    Hashes word tokens into a fixed number of buckets, so texts sharing words get similar
    vectors. It has no idea about meaning or translation; never use it in production.
    """

    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in re.findall(r"\w+", text.lower()):
            bucket = int.from_bytes(hashlib.blake2b(token.encode(), digest_size=4).digest(), "big")
            vec[bucket % self._dim] += 1.0
        return _normalise(vec)


def _normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class CloudflareEmbedder:
    """BGE-M3 (multilingual, 1024-d) on Cloudflare Workers AI, free tier (flag 15).

    Used for both law passages (at ingest) and queries. Cloudflare does not train on or
    otherwise reuse request content (docs: workers-ai/platform/data-usage).
    """

    MODEL = "@cf/baai/bge-m3"
    BATCH = 50  # texts per request

    def __init__(self, account_id: str, api_token: str, client: httpx.Client | None = None) -> None:
        self._url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{self.MODEL}"
        )
        self._headers = {"Authorization": f"Bearer {api_token}"}
        self._client = client or httpx.Client(timeout=30.0)

    @property
    def dim(self) -> int:
        return 1024

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH):
            batch = list(texts[start : start + self.BATCH])
            resp = self._client.post(self._url, headers=self._headers, json={"text": batch})
            body = (
                resp.json()
                if resp.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            if resp.status_code != 200 or not body.get("success"):
                errors = body.get("errors") or [{"message": resp.text[:200]}]
                raise RuntimeError(
                    f"Cloudflare embedding failed (HTTP {resp.status_code}): {errors}"
                )
            data = body["result"]["data"]
            if len(data) != len(batch) or any(len(v) != self.dim for v in data):
                raise RuntimeError("Cloudflare embedding returned an unexpected shape")
            vectors.extend(_normalise([float(x) for x in v]) for v in data)
        return vectors


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedder == "hash":
        return HashEmbedder()
    if not (settings.cloudflare_account_id and settings.cloudflare_api_token):
        raise ValueError("EMBEDDER=cloudflare needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN")
    return CloudflareEmbedder(
        settings.cloudflare_account_id, settings.cloudflare_api_token.get_secret_value()
    )
