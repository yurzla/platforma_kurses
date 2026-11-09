"""Рендеринг Markdown-содержимого шагов для web-интерфейса."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt
from markupsafe import Markup

# Тело шага из импортированного Stepik-контента — полноценный HTML. Такие
# тела отдаём без Markdown-обработки, чтобы не менять внешний вид.
_BLOCK_HTML = re.compile(
    r"^\s*<(?:p|div|h[1-6]|ul|ol|li|table|thead|tbody|tfoot|tr|td|th|pre|"
    r"blockquote|iframe|video|img|figure|figcaption|section|article|details|"
    r"summary|hr|br)\b",
    re.IGNORECASE | re.MULTILINE,
)

_markdown = MarkdownIt("commonmark", {"html": True, "breaks": True})


def render_step_body(text: str | None) -> Markup:
    """Возвращает безопасный HTML для тела шага."""
    if not text or not text.strip():
        return Markup("")
    if _BLOCK_HTML.search(text):
        return Markup(text)
    return Markup(_markdown.render(text))
