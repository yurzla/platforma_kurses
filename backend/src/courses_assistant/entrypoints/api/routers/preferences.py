"""Предпочтения текущего пользователя для персонализации обучения."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from courses_assistant.container import Container
from courses_assistant.domain.models import LearningPreferences, User
from courses_assistant.entrypoints.api.dependencies import get_container, require_user
from courses_assistant.entrypoints.api.schemas import (
    LearningPreferencesRead,
    LearningPreferencesUpdate,
)

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


def _preferred_level(value: str | None) -> Literal["beginner", "intermediate", "advanced"] | None:
    if value == "beginner":
        return "beginner"
    if value == "intermediate":
        return "intermediate"
    if value == "advanced":
        return "advanced"
    return None


def _read(value: LearningPreferences | None) -> LearningPreferencesRead:
    if value is None:
        return LearningPreferencesRead()
    return LearningPreferencesRead(
        interests=value.interests,
        goals=value.goals,
        preferred_level=_preferred_level(value.preferred_level),
    )


@router.get("/me", response_model=LearningPreferencesRead)
async def get_preferences(
    user: User = Depends(require_user), container: Container = Depends(get_container)
) -> LearningPreferencesRead:
    async with container.uow_factory() as uow:
        return _read(await uow.preferences.get(user.id))


@router.patch("/me", response_model=LearningPreferencesRead)
async def save_preferences(
    payload: LearningPreferencesUpdate,
    user: User = Depends(require_user),
    container: Container = Depends(get_container),
) -> LearningPreferencesRead:
    value = LearningPreferences(
        user_id=user.id,
        interests=(payload.interests or "").strip() or None,
        goals=(payload.goals or "").strip() or None,
        preferred_level=payload.preferred_level,
    )
    async with container.uow_factory() as uow:
        return _read(await uow.preferences.save(value))
