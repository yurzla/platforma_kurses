"""Хранение импортированных вариантов ответов для choice-шагов.

Revision ID: 0007_choice_options
Revises: 0006_refresh_tokens
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import Boolean, Column, inspect, text

from courses_assistant.adapters.persistence.orm import (
    ChoiceQuestionMetadataORM,
    StepChoiceOptionORM,
)

revision: str = "0007_choice_options"
down_revision: str | None = "0006_refresh_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    ChoiceQuestionMetadataORM.__table__.create(bind=bind, checkfirst=True)
    StepChoiceOptionORM.__table__.create(bind=bind, checkfirst=True)
    columns = {column["name"] for column in inspect(bind).get_columns("choice_question_metadata")}
    if "is_multiple_choice" not in columns:
        op.add_column(
            "choice_question_metadata",
            Column("is_multiple_choice", Boolean(), nullable=False, server_default="false"),
        )
    bind.execute(
        text(
            """
            UPDATE choice_question_metadata qm
            SET is_multiple_choice = COALESCE(
                (sc.options -> 'options' ->> 'is_multiple_choice')::boolean,
                false
            )
            FROM step_contents sc
            WHERE sc.step_id = qm.step_id
            """
        )
    )


def downgrade() -> None:
    StepChoiceOptionORM.__table__.drop(bind=op.get_bind(), checkfirst=True)
    ChoiceQuestionMetadataORM.__table__.drop(bind=op.get_bind(), checkfirst=True)
