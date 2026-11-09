"""Интеграционный тест рекомендателя курсов (требует PostgreSQL + pgvector).

Запуск: INTEGRATION_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from courses_assistant.adapters.persistence.orm import (
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
)
from courses_assistant.adapters.persistence.repositories import SqlCourseRecommender

DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="INTEGRATION_DATABASE_URL не задан"),
]

DIMENSION = 768


def _one_hot(index: int) -> list[float]:
    vector = [0.0] * DIMENSION
    vector[index] = 1.0
    return vector


async def test_similar_courses_ranks_by_embedding() -> None:
    assert DATABASE_URL is not None
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    marker = uuid.uuid4().hex
    course_ids: list[int] = []

    try:
        async with session_factory() as session:
            for title, vector in (
                (f"JS курс {marker}", _one_hot(0)),
                (f"Go курс {marker}", _one_hot(1)),
            ):
                course = CourseORM(title=title, description="описание", is_published=True)
                session.add(course)
                await session.flush()
                chunk = ContentChunkORM(
                    course_id=course.id,
                    chunk_text=title,
                    chunk_index=0,
                    source_type="course_description",
                )
                session.add(chunk)
                await session.flush()
                session.add(
                    ChunkEmbeddingORM(
                        chunk_id=chunk.id, model_name="test-model", embedding=vector
                    )
                )
                course_ids.append(course.id)
            await session.commit()

        uow_session = session_factory()
        try:
            recommender = SqlCourseRecommender(uow_session)
            matches = await recommender.similar_courses(
                _one_hot(0), model_name="test-model", limit=10
            )
        finally:
            await uow_session.close()

        ranked = [m.course_id for m in matches]
        assert ranked[0] == course_ids[0]
        assert course_ids[1] in ranked
        assert matches[0].score > 0.5
        js_match = next(m for m in matches if m.course_id == course_ids[0])
        assert js_match.description == "описание"
    finally:
        async with session_factory() as session:
            if course_ids:
                chunk_ids = list(
                    (
                        await session.execute(
                            select(ContentChunkORM.id).where(
                                ContentChunkORM.course_id.in_(course_ids)
                            )
                        )
                    ).scalars()
                )
                if chunk_ids:
                    await session.execute(
                        delete(ChunkEmbeddingORM).where(
                            ChunkEmbeddingORM.chunk_id.in_(chunk_ids)
                        )
                    )
                await session.execute(
                    delete(ContentChunkORM).where(ContentChunkORM.course_id.in_(course_ids))
                )
                await session.execute(delete(CourseORM).where(CourseORM.id.in_(course_ids)))
                await session.commit()
        await engine.dispose()
