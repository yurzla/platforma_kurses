"""Тесты нормализации пустых строк в ответе."""

from __future__ import annotations

from courses_assistant.domain.formatting import normalize_answer_spacing


def test_inserts_blank_line_between_adjacent_items() -> None:
    answer = "- [«A»](/courses/1) — описание\n- [«B»](/courses/2) — описание"
    assert normalize_answer_spacing(answer) == (
        "- [«A»](/courses/1) — описание\n\n- [«B»](/courses/2) — описание"
    )


def test_collapses_multiple_blank_lines() -> None:
    answer = "- A\n\n\n\n- B"
    assert normalize_answer_spacing(answer) == "- A\n\n- B"


def test_keeps_single_blank_line_between_items() -> None:
    answer = "- A\n\n- B"
    assert normalize_answer_spacing(answer) == answer


def test_inserts_blank_line_before_sources_block() -> None:
    answer = "- A\nИсточники: [«A»](/courses/1)"
    assert normalize_answer_spacing(answer) == "- A\n\nИсточники: [«A»](/courses/1)"


def test_separates_paragraph_and_list() -> None:
    answer = "Вступление.\n- A\n- B\nИтог."
    assert normalize_answer_spacing(answer) == "Вступление.\n\n- A\n\n- B\n\nИтог."


def test_keeps_list_item_continuation() -> None:
    answer = "- A\n  продолжение пункта"
    assert normalize_answer_spacing(answer) == answer


def test_keeps_nested_items_without_blank_line() -> None:
    answer = "- A\n  - B"
    assert normalize_answer_spacing(answer) == answer


def test_code_block_untouched() -> None:
    answer = "Пример:\n```\n1. A\n2. B\n```\nГотово."
    assert normalize_answer_spacing(answer) == answer


def test_paragraphs_are_not_merged_or_split() -> None:
    answer = "Первая строка.\nВторая строка."
    assert normalize_answer_spacing(answer) == answer


def test_empty_answer_is_returned_as_is() -> None:
    assert normalize_answer_spacing("") == ""


def test_splits_inline_sources_label() -> None:
    answer = "Вы можете выбрать курс. Источники: [«A»](/courses/1), [«B»](/courses/2)"
    assert normalize_answer_spacing(answer) == (
        "Вы можете выбрать курс.\n\nИсточники: [«A»](/courses/1), [«B»](/courses/2)"
    )


def test_splits_inline_sources_label_after_list() -> None:
    answer = "- A\n- B\nИтог. Источники: [«A»](/courses/1)"
    assert normalize_answer_spacing(answer) == "- A\n\n- B\n\nИтог.\n\nИсточники: [«A»](/courses/1)"


def test_does_not_split_sources_label_in_code_block() -> None:
    answer = "Пример:\n```\nтекст Источники: не метка\n```"
    assert normalize_answer_spacing(answer) == answer

