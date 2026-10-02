from haqqi.rag.lawdata import chunk_id, load_chunks, load_law_pack


def test_chunk_id_format() -> None:
    assert chunk_id("fdl33-2021", 51, 2) == "fdl33-2021:art51:cl2"
    assert chunk_id("fdl33-2021", 53, None) == "fdl33-2021:art53"


def test_chunk_ids_are_unique() -> None:
    ids = [c.id for c in load_chunks()]
    assert len(ids) == len(set(ids))


def test_law_pack_has_ten_topics_each_pointing_at_real_chunks() -> None:
    pack = load_law_pack()
    known = {c.id for c in load_chunks()}

    assert len(pack.topics) == 10
    for topic, entry in pack.topics.items():
        assert entry.chunk_ids, topic
        assert set(entry.chunk_ids) <= known, topic


def test_gratuity_article_51_has_eight_clauses() -> None:
    art51 = [c for c in load_chunks() if c.article_no == 51]
    assert [c.clause_no for c in art51] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert "twenty-one (21) days" in art51[1].text_en


def test_pack_expands_related_and_always_topics() -> None:
    pack = load_law_pack()

    ids = pack.chunk_ids_for(["termination"])

    assert ids[0] == "fdl33-2021:art42:cl3"  # the requested topic comes first
    assert "fdl33-2021:art43:cl3" in ids  # related: notice_pay
    assert "fdl33-2021:art51:cl2" in ids  # related: gratuity
    assert "fdl33-2021:art54:cl9" in ids  # always: time_limit
    assert len(ids) == len(set(ids))


def test_pack_ignores_unknown_issue_types() -> None:
    pack = load_law_pack()
    assert pack.chunk_ids_for(["other"]) == pack.chunk_ids_for([])
