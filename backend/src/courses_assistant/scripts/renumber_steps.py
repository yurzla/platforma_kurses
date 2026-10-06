"""Перенумерация шагов внутри уроков (position с 1 подряд).

Пример: python -m courses_assistant.scripts.renumber_steps
"""

from __future__ import annotations

import asyncio

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.config import get_settings

app = typer.Typer(help="Перенумерация шагов внутри уроков.")


async def renumber_step_positions(conn: AsyncConnection, course_id: int | None = None) -> int:
    """Присваивает шагам position с 1 подряд внутри каждого урока.

    Порядок сохраняется по текущим (position, id). При ``course_id``
    обрабатываются только уроки указанного курса.
    """
    course_filter = ""
    params: dict[str, int] = {}
    if course_id is not None:
        course_filter = """
            WHERE s.lesson_id IN (
                SELECT l.id FROM lessons l
                JOIN sections sec ON l.section_id = sec.id
                WHERE sec.course_id = :course_id
            )
        """
        params["course_id"] = course_id
    result = await conn.execute(
        text(
            f"""
            WITH ranked AS (
                SELECT s.id,
                       row_number() OVER (
                           PARTITION BY s.lesson_id ORDER BY s.position, s.id
                       ) AS rn
                FROM steps s
                {course_filter}
            )
            UPDATE steps
            SET position = ranked.rn
            FROM ranked
            WHERE steps.id = ranked.id
              AND steps.position IS DISTINCT FROM ranked.rn
            """
        ),
        params,
    )
    return int(result.rowcount or 0)


async def _run() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            changed = await renumber_step_positions(conn)
        typer.echo(f"Перенумеровано шагов: {changed}.")
    finally:
        await engine.dispose()


@app.command()
def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    app()
