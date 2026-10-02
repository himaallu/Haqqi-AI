"""`python -m haqqi.ingest`: rebuild the law search index in DATABASE_URL."""

import sys

import psycopg

from haqqi.config import get_settings
from haqqi.rag.embed import get_embedder
from haqqi.rag.ingest import ingest


def main() -> int:
    settings = get_settings()
    if not settings.database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 1
    with psycopg.connect(settings.database_url) as conn:
        count = ingest(conn, get_embedder(settings.embedder))
    print(f"ingested {count} law chunks (embedder: {settings.embedder})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
