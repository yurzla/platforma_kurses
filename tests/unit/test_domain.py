"""Тесты доменного слоя."""

from __future__ import annotations

from courses_assistant.domain.catalog import CourseSummary
from courses_assistant.domain.context import build_context
from courses_assistant.domain.models import ChatMessage, RetrievedChunk, Role
from courses_assistant.domain.prompts import (
    build_answer_messages,
    build_course_catalog,
    build_rewrite_prompt,
)


def _chunk(chunk_id: int, lesson: str | None = "Урок 1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=f"текст {chunk_id}",
        source_type="theory",
        lesson=lesson,
        distance=0.1,
    )


def test_build_context_numbers_sources() -> None:
    context = build_context([_chunk(1), _chunk(2)])
    assert "[Источник 1]" in context
    assert "[Источник 2]" in context
    assert "Урок 1" in context


def test_build_context_handles_missing_lesson() -> None:
    context = build_context([_chunk(1, lesson=None)])
    assert "Без названия" in context


def test_build_answer_messages_include_history_and_question() -> None:
    history = [
        ChatMessage(session_id=1, role=Role.USER, content="привет"),
        ChatMessage(session_id=1, role=Role.ASSISTANT, content="здравствуйте"),
    ]
    messages = build_answer_messages("что такое x?", "контекст", history)
    assert messages[0].role == Role.SYSTEM
    assert messages[1].content == "привет"
    assert messages[2].content == "здравствуйте"
    assert messages[-1].role == Role.USER
    assert messages[-1].content == "что такое x?"


def test_build_course_catalog_marks_enrolled() -> None:
    catalog = build_course_catalog(
        [
            CourseSummary(id=1, title="Python", description="Основы языка", enrolled=True),
            CourseSummary(id=2, title="Go", description=None),
        ]
    )
    assert "«Python»" in catalog
    assert "Основы языка" in catalog
    assert "(вы записаны)" in catalog
    assert "«Go»" in catalog


def test_build_answer_messages_include_catalog() -> None:
    messages = build_answer_messages("какой курс?", "контекст", catalog="- «Python»")
    assert "КАТАЛОГ КУРСОВ ПЛАТФОРМЫ" in messages[0].content
    assert "«Python»" in messages[0].content


def test_system_prompt_requests_markdown() -> None:
    messages = build_answer_messages("вопрос", "контекст")
    assert "Markdown" in messages[0].content
    assert "**жирным**" in messages[0].content


def test_build_rewrite_prompt_without_history_returns_question() -> None:
    assert build_rewrite_prompt("вопрос", []) == "вопрос"


def test_build_rewrite_prompt_with_history() -> None:
    history = [ChatMessage(session_id=1, role=Role.USER, content="старый вопрос")]
    prompt = build_rewrite_prompt("новый вопрос", history)
    assert "старый вопрос" in prompt
    assert "новый вопрос" in prompt
