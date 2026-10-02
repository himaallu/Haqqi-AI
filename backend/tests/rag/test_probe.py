from haqqi.rag.probe import QUERIES, ProbeQuery, rank_of, report
from haqqi.rag.retrieve import RetrievedChunk


def chunk(cid: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid, article_no=0, clause_no=None, title="", text_en="", text_ar="", source="search"
    )


def test_rank_matches_whole_article_not_prefix_lookalikes() -> None:
    results = [
        chunk("fdl33-2021:art510"),
        chunk("fdl33-2021:art5:cl1"),
        chunk("fdl33-2021:art51:cl2"),
    ]
    assert rank_of(results, "fdl33-2021:art51") == 3
    assert rank_of(results, "fdl33-2021:art53") is None


def test_report_counts_hits_in_top_five() -> None:
    q = ProbeQuery("en", "gratuity", "fdl33-2021:art51")
    late = [chunk(f"fdl33-2021:art{i}") for i in range(1, 6)] + [chunk("fdl33-2021:art51:cl1")]

    text = report([(q, [chunk("fdl33-2021:art51:cl2")]), (q, late)], "hash")

    assert "top 5: 1/2" in text
    assert "| 2 | en | gratuity | art51 | 6 |" in text


def test_probe_set_covers_english_hindi_and_arabic() -> None:
    assert len(QUERIES) == 10
    assert {q.lang for q in QUERIES} == {"en", "hi", "ar"}
