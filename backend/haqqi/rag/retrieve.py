"""Hybrid law retrieval: dense (pgvector) + full-text (English and Arabic), fused with RRF,
then topped up with the issue-type Law Pack (task 2.7)."""

from collections.abc import Sequence
from typing import Literal

import psycopg
from pydantic import BaseModel

from haqqi.rag.embed import Embedder
from haqqi.rag.ingest import vector_literal
from haqqi.rag.lawdata import LawPack

RRF_K = 60
CANDIDATES = 20  # per ranker, before fusion
TOP_K = 8


class RetrievedChunk(BaseModel):
    id: str
    article_no: int
    clause_no: int | None
    title: str
    text_en: str
    text_ar: str
    source: Literal["search", "pack"]


def rrf(rankings: Sequence[Sequence[str]], k: int = RRF_K) -> list[str]:
    """Reciprocal rank fusion: score(id) = sum over rankings of 1 / (k + rank)."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    # Ties keep first-seen order, so results are deterministic.
    order = {item: i for i, item in enumerate(scores)}
    return sorted(scores, key=lambda item: (-scores[item], order[item]))


def merge_with_pack(fused: Sequence[str], pack_ids: Sequence[str], top_k: int = TOP_K) -> list[str]:
    """Top `top_k` search hits, then every Law Pack chunk not already included."""
    picked = list(dict.fromkeys(fused))[:top_k]
    return picked + [i for i in dict.fromkeys(pack_ids) if i not in picked]


def dense_ranking(conn: psycopg.Connection, query_vec: Sequence[float], limit: int) -> list[str]:
    rows = conn.execute(
        "SELECT id FROM law_chunks WHERE embedding IS NOT NULL "
        "ORDER BY embedding <=> %s::vector LIMIT %s",
        (vector_literal(query_vec), limit),
    ).fetchall()
    return [r[0] for r in rows]


def fulltext_ranking(conn: psycopg.Connection, query: str, limit: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT id FROM law_chunks,
               websearch_to_tsquery('english', %(q)s) AS qe,
               websearch_to_tsquery('arabic', %(q)s) AS qa
        WHERE tsv_en @@ qe OR tsv_ar @@ qa
        ORDER BY greatest(ts_rank(tsv_en, qe), ts_rank(tsv_ar, qa)) DESC, id
        LIMIT %(limit)s
        """,
        {"q": query, "limit": limit},
    ).fetchall()
    return [r[0] for r in rows]


def fetch_chunks(
    conn: psycopg.Connection, ids: Sequence[str]
) -> dict[str, tuple[int, int | None, str, str, str]]:
    rows = conn.execute(
        "SELECT id, article_no, clause_no, title, text_en, text_ar FROM law_chunks "
        "WHERE id = ANY(%s)",
        (list(ids),),
    ).fetchall()
    return {r[0]: (r[1], r[2], r[3], r[4], r[5]) for r in rows}


def retrieve(
    conn: psycopg.Connection,
    query: str,
    embedder: Embedder,
    pack: LawPack,
    issue_types: Sequence[str] = (),
    top_k: int = TOP_K,
) -> list[RetrievedChunk]:
    (query_vec,) = embedder.embed([query])
    fused = rrf(
        [dense_ranking(conn, query_vec, CANDIDATES), fulltext_ranking(conn, query, CANDIDATES)]
    )
    pack_ids = pack.chunk_ids_for(list(issue_types))
    ids = merge_with_pack(fused, pack_ids, top_k)
    searched = set(fused[:top_k])
    rows = fetch_chunks(conn, ids)
    return [
        RetrievedChunk(
            id=i,
            article_no=rows[i][0],
            clause_no=rows[i][1],
            title=rows[i][2],
            text_en=rows[i][3],
            text_ar=rows[i][4],
            source="search" if i in searched else "pack",
        )
        for i in ids
        if i in rows  # a pack id missing from the index is skipped, never invented
    ]
