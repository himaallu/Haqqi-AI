"""Rebuild the law search index (law_chunks) from data/law/*.json."""

from collections.abc import Sequence
from pathlib import Path

import psycopg

from haqqi.rag.embed import Embedder
from haqqi.rag.lawdata import DATA_DIR, LawChunk, load_chunks


def vector_literal(vec: Sequence[float]) -> str:
    """pgvector text form, e.g. [0.1,0.2]. Lets us insert without an extra driver dependency."""
    return "[" + ",".join(f"{v:.7f}" for v in vec) + "]"


def embedding_text(chunk: LawChunk) -> str:
    return " ".join(part for part in (chunk.title, chunk.text_en, chunk.text_ar) if part)


def ingest(conn: psycopg.Connection, embedder: Embedder, data_dir: Path = DATA_DIR) -> int:
    """Replace every row in law_chunks with the current data files. Idempotent; one transaction."""
    chunks = load_chunks(data_dir)
    vectors = embedder.embed([embedding_text(c) for c in chunks])
    with conn.transaction():
        conn.execute("DELETE FROM law_chunks")
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO law_chunks (id, law_id, article_no, clause_no, title, topic_tags,
                                        text_en, text_ar, source_url, effective_date, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                """,
                [
                    (
                        c.id,
                        c.law_id,
                        c.article_no,
                        c.clause_no,
                        c.title,
                        c.topic_tags,
                        c.text_en,
                        c.text_ar,
                        c.source_url,
                        c.effective_date,
                        vector_literal(v),
                    )
                    for c, v in zip(chunks, vectors, strict=True)
                ],
            )
    return len(chunks)
