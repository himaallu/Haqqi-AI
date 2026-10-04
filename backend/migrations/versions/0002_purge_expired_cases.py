"""Hourly purge of expired cases with pg_cron (task 8.6), where the server offers it.

Supabase has pg_cron; the local pgvector image does not, so there this is a no-op and
`python -m haqqi.purge` does the same job by hand.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-04
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pg_cron') THEN
                CREATE EXTENSION IF NOT EXISTS pg_cron;
                PERFORM cron.schedule(
                    'haqqi-purge-expired-cases',
                    '17 * * * *',
                    'DELETE FROM public.cases WHERE expires_at <= now()'
                );
            ELSE
                RAISE NOTICE 'pg_cron is not available: run python -m haqqi.purge instead';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'cron') THEN
                PERFORM cron.unschedule(jobid)
                FROM cron.job
                WHERE jobname = 'haqqi-purge-expired-cases';
            END IF;
        END
        $$;
        """
    )
