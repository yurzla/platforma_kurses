"""Формирование выгрузки диалога с ассистентом (Markdown).

Модуль не зависит от фреймворков: получает доменные сообщения и метаданные сессии,
возвращает текст и готовые блоки для PDF-адаптера.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from courses_assistant.domain.models import ChatMessage

_ROLE_TITLES = {"user": "Вопрос", "assistant": "Ответ"}

_NO_COURSE_TITLE = "все курсы"


@dataclass(frozen=True, slots=True)
class DialogMeta:
    """Метаданные выгружаемого диалога."""

    session_id: int
    course_title: str | None
    started_at: datetime
    participant: str


@dataclass(frozen=True, slots=True)
class DialogBlock:
    """Одно сообщение диалога, подготовленное к выгрузке."""

    title: str
    text: str
    created_at: datetime | None
    sources: tuple[str, ...] = ()


def format_moment(value: datetime | None) -> str:
    """Форматирует момент времени в UTC для выгрузки."""
    if value is None:
        return ""
    moment = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%d.%m.%Y %H:%M UTC")


def collect_sources(sources: list[dict] | None) -> tuple[str, ...]:
    """Собирает уникальные подписи источников ответа (курс + ссылка)."""
    seen: list[str] = []
    for source in sources or []:
        title = source.get("course_title") or source.get("lesson") or ""
        url = source.get("course_url") or (
            f"/courses/{source['course_id']}" if source.get("course_id") else ""
        )
        label = f"«{title}»" if title else ""
        if label and url:
            item = f"{label} ({url})"
        elif label or url:
            item = label or str(url)
        else:
            continue
        if item not in seen:
            seen.append(item)
    return tuple(seen)


def build_dialog(messages: list[ChatMessage]) -> list[DialogBlock]:
    """Превращает сообщения сессии в блоки выгрузки в хронологическом порядке."""
    blocks: list[DialogBlock] = []
    for message in messages:
        role = str(message.role)
        blocks.append(
            DialogBlock(
                title=_ROLE_TITLES.get(role, role.capitalize() or "Сообщение"),
                text=message.content,
                created_at=message.created_at,
                sources=collect_sources(message.sources),
            )
        )
    return blocks


def render_markdown(meta: DialogMeta, blocks: list[DialogBlock]) -> str:
    """Рендерит диалог в Markdown-файл."""
    course = f"«{meta.course_title}»" if meta.course_title else _NO_COURSE_TITLE
    lines = [
        "# Диалог с ассистентом",
        "",
        f"- **Курс:** {course}",
        f"- **Начало:** {format_moment(meta.started_at)}",
        f"- **Участник:** {meta.participant}",
        f"- **Сессия:** #{meta.session_id}",
        "",
        "---",
        "",
    ]
    if not blocks:
        lines.append("_В диалоге пока нет сообщений._")
    for block in blocks:
        lines.append(f"### {block.title}")
        if block.created_at is not None:
            lines.extend(["", f"_{format_moment(block.created_at)}_"])
        lines.extend(["", block.text.strip(), ""])
        if block.sources:
            lines.extend([f"**Источники:** {', '.join(block.sources)}", ""])
    return "\n".join(lines).rstrip() + "\n"


def dialog_filename(meta: DialogMeta, extension: str) -> str:
    """Имя файла выгрузки: dialog-<id>-<YYYY-MM-DD>.<ext>."""
    started = meta.started_at
    moment = started if started.tzinfo is not None else started.replace(tzinfo=UTC)
    return f"dialog-{meta.session_id}-{moment.date().isoformat()}.{extension}"
