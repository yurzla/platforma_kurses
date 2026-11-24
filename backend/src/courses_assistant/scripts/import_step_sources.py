"""Импорт ключей ответов (step-sources) из Stepik в таблицу step_sources.

Требуется токен с доступом к step-sources (автор/преподаватель курса).
Пример: python -m courses_assistant.scripts.import_step_sources --token "$access_token"
"""

from __future__ import annotations

import asyncio
import json

import httpx
import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.config import get_settings

app = typer.Typer(help="Импорт step-sources из Stepik.")

BASE = "https://stepik.org/api"
CONCURRENCY = 8


async def _has_access(client: httpx.AsyncClient, token: str) -> bool:
    response = await client.get(
        f"{BASE}/step-sources",
        params={"limit": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code != 200:
        return False
    return bool(response.json().get("step-sources"))


async def _fetch_sources(
    client: httpx.AsyncClient,
    token: str,
    ext_step_id: int,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    async with semaphore:
        response = await client.get(
            f"{BASE}/step-sources",
            params={"step": ext_step_id},
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        return None
    items = response.json().get("step-sources", [])
    if not items:
        return None
    item = items[0]
    return item.get("block") or item


async def _store(conn: AsyncConnection, step_id: int, block: dict) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO step_sources (step_id, source_type, payload, fetched_at)
            VALUES (:step_id, 'step-source', CAST(:payload AS jsonb), now())
            ON CONFLICT (step_id) DO UPDATE
                SET payload = EXCLUDED.payload, fetched_at = now()
            """
        ),
        {"step_id": step_id, "payload": json.dumps(block)},
    )


async def _run(token: str, limit: int) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    imported = 0
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if not await _has_access(client, token):
                typer.echo(
                    "Нет доступа к step-sources: токен не является автором/преподавателем "
                    "доступных курсов. Ключи не импортированы."
                )
                return

            async with engine.begin() as conn:
                query = (
                    "SELECT id, external_id FROM steps WHERE external_id IS NOT NULL "
                    "ORDER BY id"
                )
                if limit:
                    query += " LIMIT :lim"
                result = await conn.execute(text(query), {"lim": limit} if limit else {})
                rows = result.all()

            semaphore = asyncio.Semaphore(CONCURRENCY)
            async with engine.begin() as conn:
                tasks = [
                    _fetch_sources(client, token, int(ext_step_id), semaphore)
                    for _, ext_step_id in rows
                ]
                blocks = await asyncio.gather(*tasks)
                for (step_id, _), block in zip(rows, blocks, strict=True):
                    if block is None:
                        continue
                    await _store(conn, step_id, block)
                    imported += 1
    finally:
        await engine.dispose()
    typer.echo(f"Готово: обработано шагов {len(rows)}, импортировано ключей {imported}.")


@app.command()
def main(
    token: str = typer.Option("", "--token", envvar="access_token"),
    limit: int = typer.Option(0, "--limit", help="ограничить число шагов (0 — все)"),
) -> None:
    if not token:
        raise typer.BadParameter("Не задан access_token (--token или env access_token).")
    asyncio.run(_run(token, limit))


if __name__ == "__main__":
    app()
