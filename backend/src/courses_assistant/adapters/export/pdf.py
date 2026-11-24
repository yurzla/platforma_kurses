"""PDF-выгрузка диалога: fpdf2 + встроенный шрифт DejaVuSans (кириллица)."""

from __future__ import annotations

from importlib.resources import as_file, files

from fpdf import FPDF
from fpdf.enums import WrapMode

from courses_assistant.application.chat_export import (
    DialogBlock,
    DialogMeta,
    format_moment,
)

_FONT_PACKAGE = "courses_assistant.adapters.export.fonts"
_FONT_FILE = "DejaVuSans.ttf"
_FONT_FAMILY = "DejaVu"
_MARGIN_MM = 15
_LINE_HEIGHT_MM = 6


def _add_font(pdf: FPDF, font_path: str) -> None:
    pdf.add_font(_FONT_FAMILY, "", font_path)


def _write(pdf: FPDF, text: str, *, size: int = 11, gap: float = 3.0) -> None:
    pdf.set_font(_FONT_FAMILY, size=size)
    if not text.strip():
        pdf.ln(_LINE_HEIGHT_MM)
        return
    pdf.multi_cell(
        0,
        _LINE_HEIGHT_MM,
        text,
        wrapmode=WrapMode.CHAR,
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(gap)


def _course_line(meta: DialogMeta) -> str:
    if meta.course_title:
        return f"Курс: «{meta.course_title}»"
    return "Курс: все курсы"


def render_pdf(meta: DialogMeta, blocks: list[DialogBlock]) -> bytes:
    """Рендерит диалог в PDF и возвращает байты файла."""
    font_resource = files(_FONT_PACKAGE).joinpath(_FONT_FILE)
    with as_file(font_resource) as font_path:
        return _render(meta, blocks, str(font_path))


def _render(meta: DialogMeta, blocks: list[DialogBlock], font_path: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM, _MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    _add_font(pdf, font_path)
    pdf.add_page()

    _write(pdf, "Диалог с ассистентом", size=16, gap=4)
    _write(pdf, _course_line(meta), size=10, gap=1)
    _write(pdf, f"Начало: {format_moment(meta.started_at)}", size=10, gap=1)
    _write(pdf, f"Участник: {meta.participant}", size=10, gap=1)
    _write(pdf, f"Сессия: #{meta.session_id}", size=10, gap=4)

    if not blocks:
        _write(pdf, "В диалоге пока нет сообщений.", size=10)
        return bytes(pdf.output())

    for block in blocks:
        _write(pdf, block.title, size=13, gap=1)
        if block.created_at is not None:
            _write(pdf, format_moment(block.created_at), size=9, gap=1)
        _write(pdf, block.text.strip(), size=11, gap=3)
        if block.sources:
            _write(pdf, "Источники: " + ", ".join(block.sources), size=9, gap=4)
    return bytes(pdf.output())
