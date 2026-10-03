"""Load the law corpus and the issue-type Law Pack from data/law/*.json."""

import json
import os
from datetime import date
from pathlib import Path

from pydantic import BaseModel

# The repo's data/law by default; the Docker image copies it elsewhere and sets LAW_DATA_DIR.
DATA_DIR = Path(
    os.environ.get("LAW_DATA_DIR") or Path(__file__).resolve().parents[3] / "data" / "law"
)
LAW_PACK_FILE = "law_pack.json"


def chunk_id(law_id: str, article_no: int, clause_no: int | None) -> str:
    """Stable id for one article clause, e.g. `fdl33-2021:art51:cl2` (flag 14)."""
    return f"{law_id}:art{article_no}" + (f":cl{clause_no}" if clause_no else "")


class LawChunk(BaseModel):
    """One retrievable unit: a clause (or a whole article without numbered clauses)."""

    id: str
    law_id: str
    article_no: int
    clause_no: int | None
    title: str
    topic_tags: list[str]
    text_en: str
    text_ar: str
    source_url: str
    effective_date: date | None


class PackTopic(BaseModel):
    pack_id: str
    ref: str
    chunk_ids: list[str]


class LawPack(BaseModel):
    topics: dict[str, PackTopic]
    related: dict[str, list[str]]
    always: list[str]

    def chunk_ids_for(self, issue_types: list[str]) -> list[str]:
        """Chunk ids for the given issue types plus their related and always-included topics."""
        wanted: list[str] = []
        for topic in [
            *issue_types,
            *(r for t in issue_types for r in self.related.get(t, [])),
            *self.always,
        ]:
            if topic in self.topics and topic not in wanted:
                wanted.append(topic)
        ids: list[str] = []
        for topic in wanted:
            ids.extend(i for i in self.topics[topic].chunk_ids if i not in ids)
        return ids


def load_chunks(data_dir: Path = DATA_DIR) -> list[LawChunk]:
    chunks: list[LawChunk] = []
    for path in sorted(data_dir.glob("*.json")):
        if path.name == LAW_PACK_FILE:
            continue
        law = json.loads(path.read_text(encoding="utf-8"))
        for article in law["articles"]:
            for clause in article["clauses"]:
                chunks.append(
                    LawChunk(
                        id=chunk_id(law["law_id"], article["article_no"], clause["clause_no"]),
                        law_id=law["law_id"],
                        article_no=article["article_no"],
                        clause_no=clause["clause_no"],
                        title=article["title_en"],
                        topic_tags=clause.get("topic_tags", []),
                        text_en=clause["text_en"],
                        text_ar=clause.get("text_ar", ""),
                        source_url=law["source_url"],
                        effective_date=law.get("effective_date"),
                    )
                )
    return chunks


def load_law_pack(data_dir: Path = DATA_DIR) -> LawPack:
    return LawPack.model_validate_json((data_dir / LAW_PACK_FILE).read_text(encoding="utf-8"))
