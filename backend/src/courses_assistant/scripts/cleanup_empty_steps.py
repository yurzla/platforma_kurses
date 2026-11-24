"""Удаление пустых шагов (без текстового содержимого).

Пример: python -m courses_assistant.scripts.cleanup_empty_steps
"""

from __future__ import annotations

import asyncio

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.config import get_settings
from courses_assistant.scripts.renumber_steps import renumber_step_positions

app = typer.Typer(help="Удаление пустых шагов из БД.")

_EMPTY_STEPS_FILTER = """
    SELECT s.id
    FROM steps s
    WHERE NOT EXISTS (
        SELECT 1 FROM step_contents sc
        WHERE sc.step_id = s.id AND btrim(coalesce(sc.body, '')) <> ''
    )
    AND NOT EXISTS (SELECT 1 FROM content_chunks cc WHERE cc.step_id = s.id)
    AND NOT EXISTS (SELECT 1 FROM step_sources ss WHERE ss.step_id = s.id)
"""


async def _count_empty(conn: AsyncConnection) -> int:
    return int(await conn.scalar(text(f"SELECT count(*) FROM ({_EMPTY_STEPS_FILTER}) t")))


async def _delete_empty(conn: AsyncConnection) -> int:
    result = await conn.execute(text(f"DELETE FROM steps WHERE id IN ({_EMPTY_STEPS_FILTER})"))
    return int(result.rowcount or 0)


async def _run() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            before = await _count_empty(conn)
            deleted = await _delete_empty(conn)
            renumbered = await renumber_step_positions(conn)
        typer.echo(
            f"Пустых шагов найдено: {before}; удалено: {deleted}; "
            f"перенумеровано шагов: {renumbered}."
        )
    finally:
        await engine.dispose()


@app.command()
def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    app()
