"""Таблица jobs для durable-состояния асинхронных вопросов.

Revision ID: 0003_jobs
Revises: 0002_hnsw
Create Date: 2026-10-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from courses_assistant.adapters.persistence.orm import JobORM

revision: str = "0003_jobs"
down_revision: str | None = "0002_hnsw"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    JobORM.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    JobORM.__table__.drop(bind=op.get_bind(), checkfirst=True)
