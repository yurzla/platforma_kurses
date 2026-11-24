"""Интеграционные тесты read-only диагностики админки (нужен PostgreSQL).

Запуск: INTEGRATION_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
Схема должна быть применена (`alembic upgrade head`).
"""

from __future__ import annotations

import os
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses_assistant.adapters.persistence.orm import (
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
)
from courses_assistant.config import Settings
from courses_assistant.entrypoints.api.routers import admin as admin_router
from tests.fakes import FakeBroker

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="INTEGRATION_DATABASE_URL не задан"),
]


async def test_admin_debug_insights(monkeypatch) -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = Settings(gigachat_credentials="test")
    container = SimpleNamespace(
        engine=engine,
        session_factory=session_factory,
        broker=FakeBroker(),
        settings=settings,
    )

    async def fake_ollama(base_url: str, model: str, timeout: float = 3.0) -> tuple[bool, None]:
        return True, None

    monkeypatch.setattr(admin_router, "check_ollama_model", fake_ollama)

    marker = uuid.uuid4().hex
    course_id: int | None = None
    empty_course_id: int | None = None
    chunk_ids: list[int] = []
    try:
        async with session_factory() as session:
            course = CourseORM(title=f"Диагностика {marker}")
            empty_course = CourseORM(title=f"Пустой {marker}")
            session.add_all([course, empty_course])
            await session.flush()
            course_id = course.id
            empty_course_id = empty_course.id
            chunks = [
                ContentChunkORM(
                    course_id=course.id,
                    chunk_text=f"{marker} теория про python",
                    chunk_index=0,
                    source_type="theory",
                ),
                ContentChunkORM(
                    course_id=course.id,
                    chunk_text=f"{marker} задание про asyncio",
                    chunk_index=1,
                    source_type="task",
                ),
                ContentChunkORM(
                    course_id=course.id,
                    chunk_text=f"{marker} описание курса",
                    chunk_index=0,
                    source_type="course_description",
                ),
            ]
            session.add_all(chunks)
            await session.flush()
            chunk_ids = [chunk.id for chunk in chunks]
            session.add(
                ChunkEmbeddingORM(
                    chunk_id=chunks[0].id,
                    model_name=settings.embedding_model,
                    embedding=[0.0] * settings.embedding_dimension,
                )
            )
            await session.commit()

        listed = await admin_router.chunks(
            course_id=course_id,
            source_type=None,
            search=None,
            limit=50,
            offset=0,
            container=container,  # type: ignore[arg-type]
        )
        assert listed.total == 3
        assert len(listed.items) == 3
        embedded = [item for item in listed.items if item.has_embedding]
        assert len(embedded) == 1
        assert embedded[0].model_name == settings.embedding_model

        filtered = await admin_router.chunks(
            course_id=course_id,
            source_type="task",
            search=None,
            limit=50,
            offset=0,
            container=container,  # type: ignore[arg-type]
        )
        assert filtered.total == 1
        assert filtered.items[0].source_type == "task"

        searched = await admin_router.chunks(
            course_id=course_id,
            source_type=None,
            search="asyncio",
            limit=50,
            offset=0,
            container=container,  # type: ignore[arg-type]
        )
        assert searched.total == 1

        paged = await admin_router.chunks(
            course_id=course_id,
            source_type=None,
            search=None,
            limit=1,
            offset=1,
            container=container,  # type: ignore[arg-type]
        )
        assert paged.total == 3
        assert len(paged.items) == 1

        detail = await admin_router.chunk_detail(
            chunk_ids[1], container  # type: ignore[arg-type]
        )
        assert detail.id == chunk_ids[1]
        assert detail.chunk_text.endswith("задание про asyncio")
        assert detail.has_embedding is False
        assert detail.embedding_dimension is None

        embedded_detail = await admin_router.chunk_detail(
            chunk_ids[0], container  # type: ignore[arg-type]
        )
        assert embedded_detail.embedding_dimension == settings.embedding_dimension
        assert embedded_detail.embedding_created_at is not None

        with pytest.raises(HTTPException) as not_found:
            await admin_router.chunk_detail(9_999_999_999, container)  # type: ignore[arg-type]
        assert not_found.value.status_code == 404

        summary = await admin_router.index_summary(container)  # type: ignore[arg-type]
        assert summary.model_name == settings.embedding_model
        assert summary.dimension == settings.embedding_dimension
        assert summary.total_chunks >= 3
        assert summary.chunks_without_embedding >= 2
        assert summary.by_source_type.get("theory", 0) >= 1
        assert summary.by_source_type.get("task", 0) >= 1
        course_summary = next(item for item in summary.courses if item.id == course_id)
        assert course_summary.chunks == 3
        assert course_summary.description_chunks == 1
        assert course_summary.step_chunks == 2
        assert course_summary.embeddings == 1
        assert course_summary.without_embedding == 2
        assert course_summary.status == "partial"

        empty_summary = next(
            item for item in summary.courses if item.id == empty_course_id
        )
        assert empty_summary.chunks == 0
        assert empty_summary.embeddings == 0
        assert empty_summary.without_embedding == 0
        assert empty_summary.status == "empty"
        assert summary.courses_without_embeddings >= 1
        assert summary.courses_without_chunks >= 1
        assert summary.queue.available is True
        assert summary.queue.length >= 0
        assert summary.queue.queue_size == (summary.queue.pending or 0) + (
            summary.queue.lag or 0
        )

        health = await admin_router.admin_health(container)  # type: ignore[arg-type]
        assert health.dependencies["postgres"] == "ok"
        assert health.dependencies["redis"] == "ok"
        assert health.dependencies["ollama"] == "ok"
        assert health.status == "ok"
        assert health.ollama_model_available is True
        assert health.settings.embedding_dimension == settings.embedding_dimension
        assert {worker.name for worker in health.workers} == {"chat", "indexer", "cron"}
    finally:
        async with session_factory() as session:
            if chunk_ids:
                await session.execute(
                    delete(ChunkEmbeddingORM).where(
                        ChunkEmbeddingORM.chunk_id.in_(chunk_ids)
                    )
                )
                await session.execute(
                    delete(ContentChunkORM).where(ContentChunkORM.id.in_(chunk_ids))
                )
            if course_id is not None:
                await session.execute(delete(CourseORM).where(CourseORM.id == course_id))
            if empty_course_id is not None:
                await session.execute(
                    delete(CourseORM).where(CourseORM.id == empty_course_id)
                )
            await session.commit()
        await engine.dispose()
