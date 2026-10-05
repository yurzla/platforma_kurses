"""Baseline: существующая схема edu_platform_kurses (без таблицы jobs).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from courses_assistant.adapters.persistence.orm import Base

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _legacy_tables() -> list:
    return [table for table in Base.metadata.sorted_tables if table.name != "jobs"]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(bind=op.get_bind(), tables=_legacy_tables())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), tables=_legacy_tables())
