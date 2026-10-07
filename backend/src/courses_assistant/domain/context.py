"""Построение RAG-контекста (чистая функция)."""

from __future__ import annotations

from collections.abc import Sequence

from courses_assistant.domain.models import RetrievedChunk


def build_context(chunks: Sequence[RetrievedChunk], max_chunks: int | None = None) -> str:
    """Собирает текстовый контекст из найденных фрагментов курса."""
    parts: list[str] = []

    selected = chunks if max_chunks is None else chunks[:max_chunks]
    for i, chunk in enumerate(selected, start=1):
        lesson = chunk.lesson or "Без названия"
        part = f"[Источник {i}]\n"
        if chunk.course_id is not None:
            part += f"Курс: «{chunk.course_title or 'Курс'}» (/courses/{chunk.course_id})\n"
        part += f"Урок: {lesson}\nТип: {chunk.source_type}\nМатериал:\n{chunk.text}"
        parts.append(part)

    return "\n\n".join(parts)
