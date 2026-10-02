"""law_chunks (hybrid search index) and cases.

Revision ID: 0001
Revises:
Create Date: 2026-10-02
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE law_chunks (
            id             text PRIMARY KEY,               -- e.g. fdl33-2021:art51:cl2
            law_id         text NOT NULL,
            article_no     integer NOT NULL,
            clause_no      integer,
            title          text NOT NULL DEFAULT '',
            topic_tags     text[] NOT NULL DEFAULT '{}',
            text_en        text NOT NULL,
            text_ar        text NOT NULL DEFAULT '',
            source_url     text NOT NULL,
            effective_date date,
            -- No fixed dimension: the embedding model is chosen in task 2.5 (flag 15).
            -- The corpus is a few hundred rows, so exact search needs no vector index.
            embedding      vector,
            tsv_en tsvector GENERATED ALWAYS AS
                (to_tsvector('english', title || ' ' || text_en)) STORED,
            tsv_ar tsvector GENERATED ALWAYS AS (to_tsvector('arabic', text_ar)) STORED
        )
        """
    )
    op.execute("CREATE INDEX law_chunks_tsv_en_idx ON law_chunks USING gin (tsv_en)")
    op.execute("CREATE INDEX law_chunks_tsv_ar_idx ON law_chunks USING gin (tsv_ar)")
    op.execute("CREATE INDEX law_chunks_topic_tags_idx ON law_chunks USING gin (topic_tags)")
    op.execute(
        """
        CREATE TABLE cases (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at  timestamptz NOT NULL DEFAULT now(),
            -- Cases auto-delete after 7 days (PRD privacy; purge job in task 8.6).
            expires_at  timestamptz NOT NULL DEFAULT now() + interval '7 days',
            language    text NOT NULL,
            status      text NOT NULL DEFAULT 'new',
            facts       jsonb NOT NULL DEFAULT '{}',
            analysis    jsonb
        )
        """
    )
    op.execute("CREATE INDEX cases_expires_at_idx ON cases (expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cases")
    op.execute("DROP TABLE IF EXISTS law_chunks")
