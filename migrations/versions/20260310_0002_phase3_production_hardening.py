"""Phase 3 production hardening schema.

Revision ID: 20260310_0002
Revises: 20260310_0001
Create Date: 2026-03-10
"""

from alembic import op


revision = "20260310_0002"
down_revision = "20260310_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open("migrations/sql/0002_phase3_production_hardening.sql", "r", encoding="utf-8").read())


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS source_sync_state;
        DROP TABLE IF EXISTS ingestion_jobs;
        DROP INDEX IF EXISTS idx_user_uploads_retention;
        DROP INDEX IF EXISTS idx_user_uploads_owner_user;
        ALTER TABLE user_uploads
            DROP COLUMN IF EXISTS owner_user_id,
            DROP COLUMN IF EXISTS retention_expires_at,
            DROP COLUMN IF EXISTS deleted_at;
        DROP INDEX IF EXISTS idx_conversations_owner_user;
        ALTER TABLE conversations DROP COLUMN IF EXISTS owner_user_id;
        """
    )
