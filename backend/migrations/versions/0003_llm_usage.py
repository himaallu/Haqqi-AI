"""Gemini calls per key, model and quota day, for the free-calls-left estimate.

The app also creates this table on first use (haqqi/usage.py), because Render doesn't run
migrations on deploy; IF NOT EXISTS lets both paths coexist.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-25
"""

from alembic import op

from haqqi.usage import DDL

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(DDL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS llm_usage")
