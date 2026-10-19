"""Юнит-тесты выгрузки диалога (Markdown и PDF)."""

from __future__ import annotations

from datetime import UTC, datetime

from courses_assistant.adapters.export.pdf import render_pdf
from courses_assistant.application.chat_export import (
    DialogMeta,
    build_dialog,
    collect_sources,
    dialog_filename,
    format_moment,
    render_markdown,
)
from courses_assistant.domain.models import ChatMessage, Role

STARTED = datetime(2026, 10, 17, 12, 30, tzinfo=UTC)
META = DialogMeta(
    session_id=7,
    course_title="Python",
    started_at=STARTED,
    participant="Студент <s@example.com>",
)


def _messages() -> list[ChatMessage]:
    return [
        ChatMessage(
            session_id=7,
            role=Role.USER,
            content="Что такое список?",
            created_at=STARTED,
        ),
        ChatMessage(
            session_id=7,
            role=Role.ASSISTANT,
            content="Список — упорядоченная коллекция.",
            created_at=STARTED,
            sources=[
                {"chunk_id": 1, "course_title": "Python", "course_url": "/courses/10"},
                {"chunk_id": 2, "course_title": "Python", "course_url": "/courses/10"},
                {"chunk_id": 3, "lesson": "Урок 1"},
            ],
        ),
    ]


def test_format_moment_treats_naive_as_utc() -> None:
    assert format_moment(datetime(2026, 10, 17, 12, 30)) == "17.10.2026 12:30 UTC"
    assert format_moment(None) == ""


def test_collect_sources_deduplicates_and_falls_back_to_course_id() -> None:
    sources = collect_sources(
        [
            {"course_title": "Python", "course_url": "/courses/10"},
            {"course_title": "Python", "course_url": "/courses/10"},
            {"course_title": "Django", "course_id": 11},
        ]
    )
    assert sources == ("«Python» (/courses/10)", "«Django» (/courses/11)")


def test_build_dialog_titles_roles() -> None:
    blocks = build_dialog(_messages())
    assert [block.title for block in blocks] == ["Вопрос", "Ответ"]
    assert blocks[1].sources[0] == "«Python» (/courses/10)"


def test_render_markdown_contains_metadata_and_dialogue() -> None:
    body = render_markdown(META, build_dialog(_messages()))
    assert body.startswith("# Диалог с ассистентом")
    assert "**Курс:** «Python»" in body
    assert "**Сессия:** #7" in body
    assert "### Вопрос" in body and "### Ответ" in body
    assert body.index("Что такое список?") < body.index("Список — упорядоченная коллекция.")
    assert "**Источники:** «Python» (/courses/10)" in body


def test_render_markdown_without_course_and_messages() -> None:
    meta = DialogMeta(
        session_id=8, course_title=None, started_at=STARTED, participant="Студент"
    )
    body = render_markdown(meta, [])
    assert "**Курс:** все курсы" in body
    assert "_В диалоге пока нет сообщений._" in body


def test_dialog_filename() -> None:
    assert dialog_filename(META, "md") == "dialog-7-2026-10-17.md"
    assert dialog_filename(META, "pdf") == "dialog-7-2026-10-17.pdf"


def test_render_pdf_produces_document() -> None:
    data = render_pdf(META, build_dialog(_messages()))
    assert data.startswith(b"%PDF")
    assert len(data) > 1000
