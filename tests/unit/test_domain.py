"""Тесты доменного слоя."""

from __future__ import annotations

from courses_assistant.domain.context import build_context
from courses_assistant.domain.models import ChatMessage, RetrievedChunk, Role
from courses_assistant.domain.prompts import (
    build_answer_messages,
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


def test_build_context_includes_course_link() -> None:
    chunk = RetrievedChunk(
        chunk_id=1,
        text="текст",
        source_type="theory",
        lesson="Урок",
        distance=0.1,
        course_id=5,
        course_title="Python",
    )
    context = build_context([chunk])
    assert "Курс: «Python» (/courses/5)" in context


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


def test_build_answer_messages_include_recommended_courses() -> None:
    messages = build_answer_messages(
        "какой курс?", "", recommended_courses="- [«Python»](/courses/1)"
    )
    content = messages[0].content
    assert "РЕКОМЕНДУЕМЫЕ КУРСЫ" in content
    assert "[«Python»](/courses/1)" in content
    assert "МАТЕРИАЛЫ КУРСА:\n" not in content


def test_build_answer_messages_forbid_self_recommendation_in_course() -> None:
    messages = build_answer_messages("вопрос", "контекст", current_course=(7, "Java"))
    content = messages[0].content
    assert "ТЕКУЩИЙ КУРС СТУДЕНТА" in content
    assert "Не предлагай" in content
    assert "[«Java»](/courses/7)" in content


def test_build_answer_messages_without_current_course() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    assert "ТЕКУЩИЙ КУРС СТУДЕНТА" not in content
    assert "Не предлагай" not in content


def test_system_prompt_requests_markdown() -> None:
    messages = build_answer_messages("вопрос", "контекст")
    assert "Markdown" in messages[0].content
    assert "**жирным**" in messages[0].content


def test_system_prompt_requests_blank_line_separation() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    block_rule = "каждый смысловой блок ответа отделяй от следующего ровно одной пустой строкой"
    items_rule = "между любыми двумя соседними пунктами списка ВСЕГДА должна быть пустая строка"
    exceptions_rule = "без исключений, даже если пункты короткие или их всего два"
    sources_rule = "перед блоком «Источники:» ВСЕГДА должна быть пустая строка"
    assert block_rule in content
    assert items_rule in content
    assert exceptions_rule in content
    assert sources_rule in content
    assert "Пример правильного оформления" in content


def test_system_prompt_grounds_only_in_provided_materials() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    assert "ТОЛЬКО" in content
    assert "/courses/ID" in content
    assert 'разделы "МАТЕРИАЛЫ КУРСА" и "РЕКОМЕНДУЕМЫЕ КУРСЫ"' in content
    assert "КАТАЛОГ КУРСОВ ПЛАТФОРМЫ" not in content


def test_system_prompt_requests_sources_block() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    expected = (
        "Источники: [«Название курса»](/courses/ID), [«Название курса 2»](/courses/ID)"
    )
    assert "«Источники:»" in content
    assert "Источники:" in content
    assert expected in content
    assert "«Источник 1»" in content
    assert "Единственное исключение" in content
    assert "которого нет в" in content
    assert "из блока «Источники» отбрасывай" in content
    assert "блок «Источники:» не добавляй" in content


def test_system_prompt_forbids_extra_courses() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    assert 'единственный источник курсов — раздел "РЕКОМЕНДУЕМЫЕ КУРСЫ"' in content
    assert "строго запрещено называть, перечислять или ссылаться на любой другой курс" in content
    assert "«Больше подходящих курсов в списке нет.»" in content
    assert "рекомендуемые курсы оформляй ТОЛЬКО маркированным списком" in content
    assert "запрещено выводить курсы одной строкой через запятую" in content

def test_system_prompt_requires_link_for_course_mention() -> None:
    content = build_answer_messages("вопрос", "контекст")[0].content
    assert "Любое упоминание курса" in content
    assert "Markdown-ссылкой [«Название»](/courses/ID)" in content
    assert "Не упоминай курс без ссылки" in content


def test_build_rewrite_prompt_without_history_returns_question() -> None:
    assert build_rewrite_prompt("вопрос", []) == "вопрос"


def test_build_rewrite_prompt_with_history() -> None:
    history = [ChatMessage(session_id=1, role=Role.USER, content="старый вопрос")]
    prompt = build_rewrite_prompt("новый вопрос", history)
    assert "старый вопрос" in prompt
    assert "новый вопрос" in prompt
