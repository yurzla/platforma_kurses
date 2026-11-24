"""Use-case подбора курсов: расширение запроса + эмбеддинг + отбор."""

from __future__ import annotations

from collections.abc import Sequence

from courses_assistant.application.ports import LLM, CourseRecommender, Embedder
from courses_assistant.domain.catalog import CourseSummary
from courses_assistant.domain.models import LearningPreferences, LLMMessage, Role
from courses_assistant.domain.prompts import build_recommendation_expansion_prompt
from courses_assistant.domain.recommender import CourseMatch, select_courses


async def rank_courses(
    question: str,
    *,
    llm: LLM,
    embedder: Embedder,
    recommender: CourseRecommender,
    model_name: str,
    top_k: int,
    margin: float,
    min_score: float,
    candidate_limit: int,
    preferences: LearningPreferences | None = None,
    completed_courses: Sequence[CourseSummary] = (),
) -> list[CourseMatch]:
    """Ранжирует курсы платформы по семантической близости к запросу."""
    expansion = await llm.generate(
        [LLMMessage(role=Role.USER, content=build_recommendation_expansion_prompt(question))],
        temperature=0.0,
    )
    profile = _preferences_search_text(preferences, completed_courses)
    search_text = " ".join(part for part in (question, expansion, profile) if part).strip()
    embedding = await embedder.embed(search_text)
    matches = await recommender.similar_courses(
        embedding,
        model_name=model_name,
        limit=candidate_limit,
        excluded_course_ids=[course.id for course in completed_courses],
    )
    return select_courses(matches, top_k=top_k, margin=margin, min_score=min_score)


def _preferences_search_text(
    preferences: LearningPreferences | None, completed_courses: Sequence[CourseSummary]
) -> str:
    values = [
        f"Интересы: {preferences.interests}" if preferences and preferences.interests else "",
        f"Цели обучения: {preferences.goals}" if preferences and preferences.goals else "",
        f"Желаемый уровень: {preferences.preferred_level}"
        if preferences and preferences.preferred_level
        else "",
    ]
    values.extend(
        f"Пройденный курс: {course.title}. {course.description or ''}"
        for course in completed_courses
    )
    return " ".join(value for value in values if value)
