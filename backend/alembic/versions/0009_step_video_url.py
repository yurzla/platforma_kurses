"""Add optional video URL for steps.

Revision ID: 0009_step_video_url
Revises: 0008_teacher_courses
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0009_step_video_url"
down_revision: str | None = "0008_teacher_courses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ``0001_baseline`` builds its tables from ORM metadata, so a fresh database
    # already has this column while an imported dump upgraded in place does not.
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("steps")}
    if "video_url" not in columns:
        op.add_column("steps", sa.Column("video_url", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("steps")}
    if "video_url" in columns:
        op.drop_column("steps", "video_url")
