"""Тесты очистки описания курса при импорте Stepik."""

from __future__ import annotations

from courses_assistant.scripts.load_stepik import (
    clean_description,
    clean_text,
    is_empty_step,
)


def test_clean_description_preserves_paragraphs_and_breaks() -> None:
    raw = "<p>Первый абзац</p><p>Второй абзац<br>строка после переноса</p>"
    assert clean_description(raw) == "Первый абзац\n\nВторой абзац\nстрока после переноса"


def test_clean_description_strips_tags_and_unescapes_entities() -> None:
    raw = "<div>Текст &amp; <strong>жирный</strong>&nbsp;конец</div>"
    out = clean_description(raw)
    assert "<" not in out and ">" not in out
    assert "&amp;" not in out and "&nbsp;" not in out
    assert "\xa0" not in out
    assert "Текст & жирный" in out


def test_clean_description_decodes_gt_and_normalizes_nbsp() -> None:
    raw = "a&nbsp;b&nbsp;&nbsp;c &gt; d"
    out = clean_description(raw)
    assert out == "a b c > d"
    assert "\xa0" not in out
    assert "&" not in out


def test_clean_description_collapses_extra_blank_lines() -> None:
    raw = "<p>А</p>\n\n\n\n<p>Б</p>"
    assert clean_description(raw) == "А\n\nБ"


def test_clean_description_handles_empty() -> None:
    assert clean_description(None) == ""
    assert clean_description("") == ""


def test_clean_text_still_collapses_to_single_line() -> None:
    assert clean_text("<p>А</p><p>Б</p>") == "А Б"


def test_clean_text_decodes_entities_and_normalizes_nbsp() -> None:
    out = clean_text("<p>А&nbsp;B</p><p>&gt; C</p>")
    assert out == "А B > C"
    assert "\xa0" not in out
    assert "&" not in out


def test_is_empty_step_detects_missing_body() -> None:
    assert is_empty_step({"name": "video"}) is True
    assert is_empty_step({"name": "video", "text": ""}) is True
    assert is_empty_step({"name": "video", "text": "   \n "}) is True


def test_is_empty_step_keeps_steps_with_content() -> None:
    assert is_empty_step({"name": "text", "text": "Материал"}) is False
    assert is_empty_step({"name": "video", "text": "<p>Описание</p>"}) is False

