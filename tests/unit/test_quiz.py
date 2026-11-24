"""Тесты доменной логики тестов (разбор ключей и оценка)."""

from __future__ import annotations

from courses_assistant.domain.quiz import (
    build_answer_key,
    correct_answer_for_display,
    grade,
    grading_mode,
)


def test_grading_mode() -> None:
    assert grading_mode("choice") == "auto"
    assert grading_mode("number") == "auto"
    assert grading_mode("string") == "auto"
    assert grading_mode("code") == "manual"
    assert grading_mode("free-answer") == "manual"


def test_choice_key_and_grade() -> None:
    block = {
        "name": "choice",
        "options": {"is_multiple_choice": False},
        "choices": [
            {"id": 1, "text": "A", "is_correct": False},
            {"id": 2, "text": "B", "is_correct": True},
        ],
    }
    key = build_answer_key("choice", block)
    assert key is not None
    assert key["correct_ids"] == [2]
    assert key["is_multiple_choice"] is False
    assert grade("choice", key, [2]) is True
    assert grade("choice", key, [1]) is False
    assert correct_answer_for_display("choice", key) == [2]


def test_number_and_string_keys() -> None:
    assert grade("number", build_answer_key("number", {"answer": "42"}), "42") is True
    assert grade("number", build_answer_key("number", {"answer": "42"}), "4") is False
    assert grade("string", build_answer_key("string", {"answer": "abc"}), "abc") is True
    assert grade("string", build_answer_key("string", {"answer": "abc"}), "x") is False


def test_missing_key_returns_none() -> None:
    assert build_answer_key("choice", {"options": {"is_multiple_choice": False}}) is None
    assert grade("choice", None, [1]) is None
    assert grade("code", {"answer": "x"}, "x") is None
