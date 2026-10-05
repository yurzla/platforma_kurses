"""Идемпотентный bootstrap схемы БД.

- Если БД пустая -> alembic upgrade head (создаёт схему).
- Если обнаружены таблицы из демо-дампа (users) -> alembic stamp baseline,
  затем alembic upgrade head (создаёт jobs и индексы, не трогая данные).
"""

from __future__ import annotations

import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from courses_assistant.config import get_settings

BASELINE_REVISION = "0001_baseline"

_SEQUENCE_SYNC_SQL = text(
    """
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN
        SELECT c.table_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND c.column_name = 'id'
          AND (c.column_default LIKE 'nextval(%' OR c.is_identity = 'YES')
    LOOP
        EXECUTE format(
            'SELECT setval(pg_get_serial_sequence(%L, ''id''), '
            'COALESCE((SELECT MAX(id) FROM %I), 1), '
            '(SELECT MAX(id) FROM %I) IS NOT NULL)',
            'public.' || r.table_name, r.table_name, r.table_name
        );
    END LOOP;
END $$;
"""
)


async def _legacy_schema_present(database_url: str) -> bool:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT to_regclass('public.users') IS NOT NULL")
            )
        return bool(exists)
    finally:
        await engine.dispose()


async def _has_alembic_version(database_url: str) -> bool:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
            )
        return bool(exists)
    finally:
        await engine.dispose()


async def _sync_sequences(database_url: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            await conn.execute(_SEQUENCE_SYNC_SQL)
    finally:
        await engine.dispose()


def main() -> None:
    settings = get_settings()
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)

    legacy = asyncio.run(_legacy_schema_present(settings.database_url))
    has_version = asyncio.run(_has_alembic_version(settings.database_url))

    if legacy and not has_version:
        command.stamp(config, BASELINE_REVISION)

    command.upgrade(config, "head")
    asyncio.run(_sync_sequences(settings.database_url))


if __name__ == "__main__":
    main()
