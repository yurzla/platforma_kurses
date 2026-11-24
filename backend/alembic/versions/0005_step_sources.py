"""Таблица step_sources (ключи ответов Stepik) и UQ прогресса.

Revision ID: 0005_step_sources
Revises: 0004_jobs_updated_at
Create Date: 2026-10-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from courses_assistant.adapters.persistence.orm import StepSourceORM

revision: str = "0005_step_sources"
down_revision: str | None = "0004_jobs_updated_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    StepSourceORM.__table__.create(bind=op.get_bind(), checkfirst=True)
    op.create_index(
        "ix_user_step_progress_user_step",
        "user_step_progress",
        ["user_id", "step_id"],
        unique=True,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_step_progress_user_step",
        table_name="user_step_progress",
        if_exists=True,
    )
    StepSourceORM.__table__.drop(bind=op.get_bind(), checkfirst=True)
