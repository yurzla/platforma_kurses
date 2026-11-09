"""Тесты рендеринга Markdown-содержимого шагов."""

from __future__ import annotations

from courses_web.markdown import render_step_body


def test_markdown_emphasis_and_link() -> None:
    html = str(render_step_body("**жирный** и [ссылка](https://example.com)"))
    assert "<strong>жирный</strong>" in html
    assert '<a href="https://example.com">ссылка</a>' in html


def test_markdown_list_and_code_block() -> None:
    ul = str(render_step_body("- один\n- два"))
    assert "<ul>" in ul
    assert "<li>один</li>" in ul
    assert "<li>два</li>" in ul

    code = str(render_step_body("```python\nprint(1)\n```"))
    assert "<pre>" in code
    assert "print(1)" in code


def test_single_line_breaks_preserved() -> None:
    html = str(render_step_body("первая строка\nвторая строка"))
    assert "<br" in html


def test_legacy_html_preserved() -> None:
    source = '<p>Старый текст</p><iframe src="https://www.youtube.com/embed/x"></iframe>'
    assert str(render_step_body(source)) == source


def test_empty_body() -> None:
    assert str(render_step_body("")) == ""
    assert str(render_step_body(None)) == ""
    assert str(render_step_body("   ")) == ""
