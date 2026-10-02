import json
import math
from collections.abc import Callable

import httpx
import pytest

from haqqi.config import Settings
from haqqi.rag.embed import CloudflareEmbedder, Embedder, HashEmbedder, get_embedder


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_hash_embedder_is_deterministic_unit_length_and_sized() -> None:
    embedder: Embedder = HashEmbedder(dim=64)

    first, second = embedder.embed(["unpaid salary for three months"] * 2)

    assert len(first) == 64
    assert first == second
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0)


def test_hash_embedder_ranks_shared_words_higher() -> None:
    q, near, far = HashEmbedder().embed(
        ["end of service gratuity", "gratuity at the end of service", "overtime on rest days"]
    )

    assert cosine(q, near) > cosine(q, far)


def test_hash_embedder_handles_empty_text() -> None:
    (vec,) = HashEmbedder(dim=8).embed([""])
    assert vec == [0.0] * 8


def _cloudflare(handler: Callable[[httpx.Request], httpx.Response]) -> CloudflareEmbedder:
    return CloudflareEmbedder(
        "acct", "tok", client=httpx.Client(transport=httpx.MockTransport(handler))
    )


def test_cloudflare_embedder_batches_and_normalises() -> None:
    seen: list[list[str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/client/v4/accounts/acct/ai/run/@cf/baai/bge-m3"
        assert request.headers["authorization"] == "Bearer tok"
        texts = json.loads(request.content)["text"]
        seen.append(texts)
        data = [[3.0, 4.0] + [0.0] * 1022 for _ in texts]
        return httpx.Response(200, json={"success": True, "result": {"data": data}})

    vectors = _cloudflare(handler).embed([f"t{i}" for i in range(CloudflareEmbedder.BATCH + 1)])

    assert [len(b) for b in seen] == [CloudflareEmbedder.BATCH, 1]
    assert len(vectors) == CloudflareEmbedder.BATCH + 1
    assert vectors[0][:2] == [0.6, 0.8]


def test_cloudflare_embedder_raises_on_api_error_without_leaking_the_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"success": False, "errors": [{"message": "Authentication error"}]}
        )

    with pytest.raises(RuntimeError, match="HTTP 401.*Authentication error") as err:
        _cloudflare(handler).embed(["x"])
    assert "tok" not in str(err.value)


def test_get_embedder_requires_cloudflare_credentials() -> None:
    with pytest.raises(ValueError, match="CLOUDFLARE_ACCOUNT_ID"):
        get_embedder(Settings(_env_file=None, embedder="cloudflare"))
    assert isinstance(get_embedder(Settings(_env_file=None, embedder="hash")), HashEmbedder)


@pytest.mark.live
def test_cloudflare_bge_m3_matches_hindi_and_arabic_to_english() -> None:
    settings = Settings()
    if settings.embedder != "cloudflare":
        pytest.skip("EMBEDDER=cloudflare not configured")
    hi, ar, en, other = get_embedder(settings).embed(
        [
            "मेरी तनख्वाह तीन महीने से नहीं मिली",
            "لم أستلم راتبي منذ ثلاثة أشهر",
            "my salary has not been paid for three months",
            "annual leave carried forward to next year",
        ]
    )
    assert len(hi) == 1024
    assert cosine(hi, en) > cosine(hi, other)
    assert cosine(ar, en) > cosine(ar, other)
