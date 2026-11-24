"""Очистка описаний курсов: декодирование HTML-сущностей и нормализация пробелов.

Пример: python -m courses_assistant.scripts.fix_course_descriptions
"""

from __future__ import annotations

import asyncio

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.config import get_settings
from courses_assistant.scripts.load_stepik import clean_description

app = typer.Typer(help="Очистка описаний курсов в БД.")


async def _fix_descriptions(conn: AsyncConnection) -> tuple[int, int]:
    rows = (await conn.execute(text("SELECT id, description FROM courses"))).all()
    changed = 0
    for course_id, description in rows:
        cleaned = clean_description(description)
        if cleaned != (description or ""):
            await conn.execute(
                text("UPDATE courses SET description = :description WHERE id = :id"),
                {"description": cleaned, "id": course_id},
            )
            changed += 1
    return len(rows), changed


async def _run() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            total, changed = await _fix_descriptions(conn)
        typer.echo(f"Проверено курсов: {total}; обновлено описаний: {changed}.")
    finally:
        await engine.dispose()


@app.command()
def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    app()
