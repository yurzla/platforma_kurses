"""Jinja2-окружение web-сервиса."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates

from courses_web.markdown import render_step_body

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def static_url(path: str) -> str:
    """URL статики с версией (mtime) — обходит кэш браузера при изменениях."""
    try:
        version = int((STATIC_DIR / path).stat().st_mtime)
    except OSError:
        version = 0
    return f"/static/{path}?v={version}"


def current_year() -> int:
    """Текущий год для футера (вычисляется при рендере)."""
    return datetime.now(UTC).year


templates.env.globals["static_url"] = static_url
templates.env.globals["current_year"] = current_year
templates.env.filters["markdown"] = render_step_body

