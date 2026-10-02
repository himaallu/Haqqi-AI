import psycopg
import pytest

from haqqi.rag.embed import HashEmbedder
from haqqi.rag.ingest import ingest
from haqqi.rag.lawdata import load_law_pack
from haqqi.rag.retrieve import fulltext_ranking, merge_with_pack, retrieve, rrf


def test_rrf_rewards_items_ranked_well_by_both_rankers() -> None:
    dense = ["a", "b", "c"]
    keyword = ["b", "c", "d"]

    fused = rrf([dense, keyword])

    # b: 1/62 + 1/61 = .0325, c: 1/63 + 1/62 = .0320, a: 1/61 = .0164, d: 1/63 = .0159
    assert fused == ["b", "c", "a", "d"]


def test_rrf_single_ranking_keeps_order() -> None:
    assert rrf([["x", "y", "z"]]) == ["x", "y", "z"]


def test_merge_with_pack_keeps_top_k_then_appends_missing_pack_chunks() -> None:
    fused = ["s1", "s2", "s3", "p1"]

    merged = merge_with_pack(fused, ["p1", "p2", "p2"], top_k=3)

    assert merged == ["s1", "s2", "s3", "p1", "p2"]


def test_merge_with_pack_does_not_duplicate_pack_hits_in_top_k() -> None:
    assert merge_with_pack(["p1", "s1"], ["p1"], top_k=8) == ["p1", "s1"]


@pytest.mark.live
def test_retrieve_end_to_end_on_real_postgres(local_db_url: str) -> None:
    # Needs a migrated local database: `make dev`, then `make test-live`.
    url = local_db_url
    embedder = HashEmbedder()
    with psycopg.connect(url) as conn:
        ingest(conn, embedder)

        results = retrieve(
            conn, "end of service gratuity basic wage", embedder, load_law_pack(), ["gratuity"]
        )

    ids = [r.id for r in results]
    assert ids[0].startswith("fdl33-2021:art51")
    assert "fdl33-2021:art54:cl9" in ids  # always-included time limit
    assert len(ids) == len(set(ids))
    assert {r.source for r in results} <= {"search", "pack"}


@pytest.mark.live
def test_fulltext_matches_when_only_some_query_words_appear(local_db_url: str) -> None:
    with psycopg.connect(local_db_url) as conn:
        ingest(conn, HashEmbedder())
        english = fulltext_ranking(conn, "gratuity qwertyuiop", 5)
        arabic = fulltext_ranking(conn, "مكافأة نهاية الخدمة كلمةغيرموجودة", 5)

    assert any(i.startswith("fdl33-2021:art51") for i in english)
    assert any(i.startswith("fdl33-2021:art51") for i in arabic)
