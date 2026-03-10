"""Initial legal rag schema.

Revision ID: 20260310_0001
Revises:
Create Date: 2026-03-10
"""

from alembic import op


revision = "20260310_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open("migrations/sql/0001_initial_legal_rag.sql", "r", encoding="utf-8").read())


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS contracts_metadata;
        DROP TABLE IF EXISTS legislation_metadata;
        DROP TABLE IF EXISTS jurisprudence_metadata;
        DROP TABLE IF EXISTS legal_entities;
        DROP TABLE IF EXISTS user_uploads;
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS conversations;
        DROP TABLE IF EXISTS retrieval_logs;
        DROP TABLE IF EXISTS citations;
        DROP TABLE IF EXISTS embeddings;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS document_versions;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS sources;
        """
    )

