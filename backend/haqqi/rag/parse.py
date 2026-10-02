"""Parse the official law pages (data/law/raw/*.md) into data/law/<law_id>.json (task 2.3).

The raw files are the uaelegislation.gov.ae article pages saved as Markdown (see SOURCES.md).
Each article becomes one record; numbered clauses become separate chunks, and the English and
Arabic texts are paired by article and clause number. Parsing the HTML text (not the PDFs) avoids
the broken Arabic glyph order of PDF extraction (flag 17).

Run: python -m haqqi.rag.parse
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from haqqi.rag.lawdata import DATA_DIR, LAW_PACK_FILE, chunk_id

RAW_DIR = DATA_DIR / "raw"

ARTICLE_EN = re.compile(r"^#### Article \((\d+)\)\s*(.*)$")
ARTICLE_AR = re.compile(r"^#### المادة \((\d+)\)\s*(.*)$")
PREVIOUS_TEXTS_AR = "النصوص السابقة"  # site marker on amended articles, not part of the title
CLAUSE = re.compile(r"^(\d+)\.\s*(.*)$", re.S)
# Zero-width and bidi marks the site sprinkles into list markers.
INVISIBLE = re.compile("[​‌‍‎‏﻿]")


@dataclass
class Article:
    article_no: int
    title: str
    intro: str = ""
    clauses: list[str] = field(default_factory=list)  # index 0 = clause 1


@dataclass(frozen=True)
class LawSource:
    law_id: str
    title_en: str
    title_ar: str
    source_url: str
    effective_date: str


LAWS = [
    LawSource(
        law_id="fdl33-2021",
        title_en="Federal Decree-Law No. 33 of 2021 Regulating Labour Relations (consolidated)",
        title_ar="مرسوم بقانون اتحادي رقم (33) لسنة 2021 بشأن تنظيم علاقات العمل",
        source_url="https://uaelegislation.gov.ae/en/legislations/1541",
        effective_date="2022-02-02",
    ),
    LawSource(
        law_id="cr1-2022",
        title_en="Cabinet Resolution No. 1 of 2022 (Executive Regulation of FDL 33/2021)",
        title_ar="قرار مجلس الوزراء رقم (1) لسنة 2022 في شأن اللائحة التنفيذية",
        source_url="https://uaelegislation.gov.ae/en/legislations/1547",
        effective_date="2022-02-02",
    ),
]


def clean(text: str) -> str:
    """Markdown paragraph → plain text: drop escapes, bold markers and invisible marks."""
    text = INVISIBLE.sub("", text)
    text = text.replace("\\", "").replace("**", "")
    return re.sub(r"[ \t]+", " ", text).strip()


def paragraphs(lines: list[str]) -> list[str]:
    paras: list[str] = []
    current: list[str] = []
    for line in [*lines, ""]:
        if line.strip():
            current.append(line.strip())
        elif current:
            paras.append(clean(" ".join(current)))
            current = []
    return [p for p in paras if p]


def parse_markdown(markdown: str, article_re: re.Pattern[str]) -> dict[int, Article]:
    """Split a law page into articles and their numbered clauses.

    A paragraph starts clause n only if it is numbered n and clause n-1 came before it, so
    numbered lists nested inside a clause are not mistaken for clauses. Other paragraphs
    (lettered sub-items, continuations) attach to the current clause, or to the intro.
    """
    articles: dict[int, Article] = {}
    blocks: list[tuple[int, str, list[str]]] = []
    for line in markdown.splitlines():
        match = article_re.match(line)
        if match:
            title = clean(match.group(2).replace(PREVIOUS_TEXTS_AR, ""))
            blocks.append((int(match.group(1)), title, []))
        elif blocks:
            if line.startswith("#### ") or line.startswith("[") or line.startswith("!["):
                blocks[-1][2].append("\0")  # end of the article body (page chrome follows)
            blocks[-1][2].append(line)
    for article_no, title, body in blocks:
        if "\0" in body:
            body = body[: body.index("\0")]
        article = Article(article_no=article_no, title=title)
        for para in paragraphs(body):
            match = CLAUSE.match(para)
            if match and int(match.group(1)) == len(article.clauses) + 1:
                article.clauses.append(match.group(2).strip())
            elif article.clauses:
                article.clauses[-1] += "\n" + para
            else:
                article.intro = f"{article.intro}\n{para}".strip()
        articles[article_no] = article
    return articles


def _with_intro(intro: str, text: str) -> str:
    return f"{intro}\n{text}" if intro else text


def pair_articles(en: dict[int, Article], ar: dict[int, Article]) -> list[dict[str, Any]]:
    """Pair English and Arabic articles clause by clause.

    The Arabic text is authoritative. If the two versions number clauses differently, the article
    is kept as a single chunk (both texts whole) rather than pairing clauses that may not match.
    """
    missing = sorted(set(en) ^ set(ar))
    if missing:
        raise ValueError(f"articles present in only one language: {missing}")
    records: list[dict[str, Any]] = []
    for no in sorted(en):
        a_en, a_ar = en[no], ar[no]
        if a_en.clauses and len(a_en.clauses) == len(a_ar.clauses):
            clauses = [
                {
                    "clause_no": i,
                    "text_en": _with_intro(a_en.intro, t_en),
                    "text_ar": _with_intro(a_ar.intro, t_ar),
                }
                for i, (t_en, t_ar) in enumerate(zip(a_en.clauses, a_ar.clauses, strict=True), 1)
            ]
        else:
            clauses = [
                {
                    "clause_no": None,
                    "text_en": _whole(a_en),
                    "text_ar": _whole(a_ar),
                }
            ]
        records.append(
            {"article_no": no, "title_en": a_en.title, "title_ar": a_ar.title, "clauses": clauses}
        )
    return records


def _whole(article: Article) -> str:
    numbered = [f"{i}. {t}" for i, t in enumerate(article.clauses, 1)]
    return "\n".join(p for p in [article.intro, *numbered] if p)


def mismatched_articles(en: dict[int, Article], ar: dict[int, Article]) -> list[int]:
    return [no for no in sorted(en) if no in ar and len(en[no].clauses) != len(ar[no].clauses)]


def topic_tags(data_dir: Path = DATA_DIR) -> dict[str, list[str]]:
    """chunk id → Law Pack topics that include it."""
    pack = json.loads((data_dir / LAW_PACK_FILE).read_text(encoding="utf-8"))
    tags: dict[str, list[str]] = {}
    for topic, entry in pack["topics"].items():
        for cid in entry["chunk_ids"]:
            tags.setdefault(cid, []).append(topic)
    return tags


def build_law(source: LawSource, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    en = parse_markdown((raw_dir / f"{source.law_id}.en.md").read_text("utf-8"), ARTICLE_EN)
    ar = parse_markdown((raw_dir / f"{source.law_id}.ar.md").read_text("utf-8"), ARTICLE_AR)
    articles = pair_articles(en, ar)
    tags = topic_tags()
    for article in articles:
        for clause in article["clauses"]:
            cid = chunk_id(source.law_id, article["article_no"], clause["clause_no"])
            clause["topic_tags"] = tags.get(cid, [])
    return {
        "law_id": source.law_id,
        "title_en": source.title_en,
        "title_ar": source.title_ar,
        "source_url": source.source_url,
        "effective_date": source.effective_date,
        "status": "official",
        "status_note": "Generated by `python -m haqqi.rag.parse` from data/law/raw "
        "(see SOURCES.md). The Arabic text prevails over the English translation.",
        "single_chunk_articles": mismatched_articles(en, ar),
        "articles": articles,
    }


def main() -> None:
    for source in LAWS:
        law = build_law(source)
        out = DATA_DIR / f"{source.law_id}.json"
        out.write_text(json.dumps(law, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n_chunks = sum(len(a["clauses"]) for a in law["articles"])
        print(
            f"{out.name}: {len(law['articles'])} articles, {n_chunks} chunks, "
            f"single-chunk articles {law['single_chunk_articles']}"
        )


if __name__ == "__main__":
    main()
