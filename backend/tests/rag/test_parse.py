import json
import re

from haqqi.rag.lawdata import DATA_DIR
from haqqi.rag.parse import (
    ARTICLE_AR,
    ARTICLE_EN,
    LAWS,
    build_law,
    pair_articles,
    parse_markdown,
)

ARABIC = re.compile(r"[؀-ۿ]")

EN_PAGE = """\
#### Index
- [Article (1) Definitions](https://example/#item1)

#### Article (1) Definitions

**State:** United Arab Emirates.

#### Article (2) Gratuity

1\\. The Worker is entitled to:

    a. 21 days for each year;

    b. 30 days after that.

2\\. Steps:

1\\. a nested list item, not clause 1

3\\. Third clause.

[Load more](https://example/#)

Translated in cooperation with
"""

AR_PAGE = """\
#### المادة (1) التعريفات

**الدولة:** الإمارات العربية المتحدة.

#### المادة (2) المكافأة     النصوص السابقة

1\\. يستحق العامل:

    ‌أ. أجر 21 يوم؛

2\\. الخطوات:

3. البند الثالث.

[حمل أكثر](https://example/#)
"""


def test_splits_numbered_clauses_and_keeps_sub_items() -> None:
    art = parse_markdown(EN_PAGE, ARTICLE_EN)[2]

    assert art.title == "Gratuity"
    assert len(art.clauses) == 3
    assert (
        art.clauses[0]
        == "The Worker is entitled to:\na. 21 days for each year;\nb. 30 days after that."
    )
    assert art.clauses[1] == "Steps:\n1. a nested list item, not clause 1"  # not a new clause 1
    assert art.clauses[2] == "Third clause."  # page chrome after the last article is cut


def test_article_without_clauses_keeps_its_text_as_intro() -> None:
    art = parse_markdown(EN_PAGE, ARTICLE_EN)[1]
    assert art.clauses == []
    assert art.intro == "State: United Arab Emirates."


def test_arabic_page_strips_amendment_marker_and_invisible_marks() -> None:
    art = parse_markdown(AR_PAGE, ARTICLE_AR)[2]

    assert art.title == "المكافأة"
    assert art.clauses[0] == "يستحق العامل:\nأ. أجر 21 يوم؛"
    assert art.clauses[2] == "البند الثالث."  # numbered without the Markdown escape


def test_pairs_languages_by_clause_or_falls_back_to_one_chunk() -> None:
    en = parse_markdown(EN_PAGE, ARTICLE_EN)
    ar = parse_markdown(AR_PAGE, ARTICLE_AR)
    records = {r["article_no"]: r for r in pair_articles(en, ar)}

    assert [c["clause_no"] for c in records[2]["clauses"]] == [1, 2, 3]
    assert records[2]["clauses"][2]["text_ar"] == "البند الثالث."
    assert records[1]["clauses"] == [
        {
            "clause_no": None,
            "text_en": "State: United Arab Emirates.",
            "text_ar": "الدولة: الإمارات العربية المتحدة.",
        }
    ]

    del ar[2].clauses[2]  # clause counts now differ → whole article as one chunk
    mismatched = {r["article_no"]: r for r in pair_articles(en, ar)}[2]
    assert [c["clause_no"] for c in mismatched["clauses"]] == [None]
    assert mismatched["clauses"][0]["text_en"].startswith("1. The Worker is entitled to:")


def test_committed_law_files_match_the_raw_sources() -> None:
    for source in LAWS:
        committed = json.loads((DATA_DIR / f"{source.law_id}.json").read_text(encoding="utf-8"))
        assert committed == build_law(source), (
            f"re-run `python -m haqqi.rag.parse` ({source.law_id})"
        )


def test_official_article_51_has_eight_bilingual_clauses() -> None:
    law = build_law(LAWS[0])
    art51 = next(a for a in law["articles"] if a["article_no"] == 51)

    assert [c["clause_no"] for c in art51["clauses"]] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert "twenty-one (21) days" in art51["clauses"][1]["text_en"]
    assert "(21) واحد وعشرين يوم" in art51["clauses"][1]["text_ar"]


def test_every_chunk_has_english_and_arabic_text() -> None:
    for source in LAWS:
        for article in build_law(source)["articles"]:
            for clause in article["clauses"]:
                where = f"{source.law_id} art {article['article_no']}({clause['clause_no']})"
                assert clause["text_en"].strip(), where
                assert ARABIC.search(clause["text_ar"]), where
                assert not ARABIC.search(clause["text_en"]), where
