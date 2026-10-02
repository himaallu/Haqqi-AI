"""Text embedders. Retrieval depends only on the `Embedder` protocol (flag 15)."""

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol


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
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def get_embedder(name: str) -> Embedder:
    if name == "hash":
        return HashEmbedder()
    raise ValueError(f"unknown embedder: {name}")
