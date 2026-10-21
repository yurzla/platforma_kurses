"""Add ownership for teacher-authored courses.

Revision ID: 0008_teacher_courses
Revises: 0007_choice_options
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0008_teacher_courses"
down_revision: str | None = "0007_choice_options"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ``0001_baseline`` builds its tables from ORM metadata. Therefore a new
    # empty database can already contain this column, whereas an imported dump
    # upgraded in place does not.
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("courses")}
    if "owner_id" not in columns:
        op.add_column("courses", sa.Column("owner_id", sa.BigInteger(), nullable=True))
    foreign_keys = inspector.get_foreign_keys("courses")
    if not any(fk.get("constrained_columns") == ["owner_id"] for fk in foreign_keys):
        op.create_foreign_key("courses_owner_id_fkey", "courses", "users", ["owner_id"], ["id"])
    indexes = {index["name"] for index in inspector.get_indexes("courses")}
    if "ix_courses_owner_id" not in indexes:
        op.create_index("ix_courses_owner_id", "courses", ["owner_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ix_courses_owner_id" in {index["name"] for index in inspector.get_indexes("courses")}:
        op.drop_index("ix_courses_owner_id", table_name="courses")
    foreign_keys = inspector.get_foreign_keys("courses")
    owner_fk = next((fk for fk in foreign_keys if fk.get("constrained_columns") == ["owner_id"]), None)
    if owner_fk and owner_fk.get("name"):
        op.drop_constraint(owner_fk["name"], "courses", type_="foreignkey")
    if "owner_id" in {column["name"] for column in inspector.get_columns("courses")}:
        op.drop_column("courses", "owner_id")
