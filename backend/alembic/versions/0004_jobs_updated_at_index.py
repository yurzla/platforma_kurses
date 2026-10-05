"""Индекс по jobs.updated_at для retention-purge.

Revision ID: 0004_jobs_updated_at
Revises: 0003_jobs
Create Date: 2026-10-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004_jobs_updated_at"
down_revision: str | None = "0003_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "idx_jobs_updated_at"


def upgrade() -> None:
    op.create_index(INDEX_NAME, "jobs", ["updated_at"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="jobs", if_exists=True)
