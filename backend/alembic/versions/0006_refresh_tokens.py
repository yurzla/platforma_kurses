"""Таблица refresh_tokens (JWT refresh-токены) для ротации и отзыва.

Revision ID: 0006_refresh_tokens
Revises: 0005_step_sources
Create Date: 2026-10-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from courses_assistant.adapters.persistence.orm import RefreshTokenORM

revision: str = "0006_refresh_tokens"
down_revision: str | None = "0005_step_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    RefreshTokenORM.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    RefreshTokenORM.__table__.drop(bind=op.get_bind(), checkfirst=True)
