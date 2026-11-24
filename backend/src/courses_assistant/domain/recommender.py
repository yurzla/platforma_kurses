"""Подбор рекомендуемых курсов по эмбеддингам (чистые функции)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from courses_assistant.domain.prompts import course_link_markdown

_RECOMMENDATION_INTENT_RE = re.compile(
    r"как(?:ой|ие|ую|ого)\s+курс"
    r"|курс(?:ы|ов|а|е)?\s+по"
    r"|посоветуй|порекомендуй|подбер\w*\s+курс"
    r"|с\s+чего\s+начать"
    r"|есть\s+ли\s+курс",
    re.IGNORECASE,
)


@dataclass(slots=True, frozen=True)
class CourseMatch:
    """Курс-кандидат с оценкой семантической близости."""

    course_id: int
    title: str
    description: str | None
    score: float


def looks_like_course_query(question: str) -> bool:
    """Похож ли вопрос на просьбу подобрать/перечислить курсы."""
    return bool(_RECOMMENDATION_INTENT_RE.search(question))


def select_courses(
    matches: Sequence[CourseMatch],
    *,
    top_k: int,
    margin: float,
    min_score: float,
) -> list[CourseMatch]:
    """Оставляет ближайшие курсы: в пределах ``margin`` от лучшего и не ниже ``min_score``."""
    if not matches or top_k <= 0:
        return []
    ranked = sorted(matches, key=lambda match: match.score, reverse=True)
    threshold = max(min_score, ranked[0].score - margin)
    return [match for match in ranked if match.score >= threshold][:top_k]


def _short_description(text: str | None, limit: int) -> str:
    if not text:
        return ""
    value = " ".join(text.split())
    if len(value) > limit:
        value = value[:limit].rstrip() + "…"
    return value


def build_recommended_courses_section(
    matches: Sequence[CourseMatch],
    *,
    description_limit: int,
) -> str:
    """Секция «РЕКОМЕНДУЕМЫЕ КУРСЫ» из кандидатов для LLM (ссылки + краткие описания)."""
    lines: list[str] = []
    for match in matches:
        line = f"- {course_link_markdown(match.title, match.course_id)}"
        description = _short_description(match.description, description_limit)
        if description:
            line += f" — {description}"
        lines.append(line)
    return "\n".join(lines)
