"""Тесты постановки задачи индексации курсов преподавателя."""

from __future__ import annotations

from types import SimpleNamespace

from courses_assistant.adapters.persistence.course_indexer import CourseDescriptionIndexer
from courses_assistant.entrypoints.api.routers.teacher import (
    _enqueue_course_index,
    _enqueue_step_index,
)
from tests.fakes import FakeBroker


async def test_enqueue_course_index_publishes_course_id() -> None:
    broker = FakeBroker()
    container = SimpleNamespace(
        broker=broker,
        settings=SimpleNamespace(stream_index="rag.index.requests", redis_stream_maxlen=42),
    )

    await _enqueue_course_index(container, 17)

    assert broker.published == [("rag.index.requests", {"course_id": 17})]


async def test_enqueue_step_index_publishes_step_upsert() -> None:
    broker = FakeBroker()
    container = SimpleNamespace(
        broker=broker,
        settings=SimpleNamespace(stream_index="rag.index.requests", redis_stream_maxlen=42),
    )

    await _enqueue_step_index(container, 18)

    assert broker.published == [("rag.index.requests", {"kind": "step_upsert", "step_id": 18})]


def test_description_index_chunking_has_overlap() -> None:
    chunks = CourseDescriptionIndexer._split_into_chunks(" ".join(str(n) for n in range(600)))

    assert len(chunks) == 2
    assert chunks[0].split()[-1] == "499"
    assert chunks[1].split()[0] == "450"
