import math

from haqqi.rag.embed import Embedder, HashEmbedder


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
