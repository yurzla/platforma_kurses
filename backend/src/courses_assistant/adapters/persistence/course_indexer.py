"""Идемпотентная индексация описания одного курса."""

from __future__ import annotations

import html
import re

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from courses_assistant.adapters.persistence.orm import (
    ChunkEmbeddingORM,
    ContentChunkORM,
    CourseORM,
    LessonORM,
    SectionORM,
    StepContentORM,
    StepORM,
)
from courses_assistant.application.ports import Embedder

_TAG = re.compile(r"<[^>]+>")


def _clean_text(value: str) -> str:
    value = _TAG.sub(" ", value)
    return " ".join(html.unescape(value).split())


class CourseDescriptionIndexer:
    """Поддерживает актуальные чанки ``course_description``."""

    def __init__(self, embedder: Embedder, model_name: str) -> None:
        self._embedder = embedder
        self._model_name = model_name

    async def index(self, session: AsyncSession, course_id: int) -> bool:
        course = await session.get(CourseORM, course_id)
        if course is None:
            return False

        chunks = self._split_into_chunks(_clean_text(f"{course.title}. {course.description or ''}"))
        existing = (
            (
                await session.execute(
                    select(ContentChunkORM)
                    .where(
                        ContentChunkORM.course_id == course_id,
                        ContentChunkORM.lesson_id.is_(None),
                        ContentChunkORM.step_id.is_(None),
                        ContentChunkORM.source_type == "course_description",
                    )
                    .order_by(ContentChunkORM.chunk_index, ContentChunkORM.id)
                )
            )
            .scalars()
            .all()
        )
        by_index = {chunk.chunk_index: chunk for chunk in existing}

        for index, chunk_text in enumerate(chunks):
            chunk = by_index.pop(index, None)
            changed = chunk is None or chunk.chunk_text != chunk_text
            if chunk is None:
                chunk = ContentChunkORM(
                    course_id=course_id,
                    lesson_id=None,
                    step_id=None,
                    chunk_text=chunk_text,
                    chunk_index=index,
                    source_type="course_description",
                )
                session.add(chunk)
                await session.flush()
            elif changed:
                chunk.chunk_text = chunk_text

            embeddings = (
                (
                    await session.execute(
                        select(ChunkEmbeddingORM).where(
                            ChunkEmbeddingORM.chunk_id == chunk.id,
                            ChunkEmbeddingORM.model_name == self._model_name,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if changed or not embeddings:
                for embedding in embeddings:
                    await session.delete(embedding)
                session.add(
                    ChunkEmbeddingORM(
                        chunk_id=chunk.id,
                        model_name=self._model_name,
                        embedding=await self._embedder.embed(chunk_text),
                    )
                )

        stale_ids = [chunk.id for chunk in by_index.values()]
        if stale_ids:
            await session.execute(
                delete(ChunkEmbeddingORM).where(ChunkEmbeddingORM.chunk_id.in_(stale_ids))
            )
            await session.execute(delete(ContentChunkORM).where(ContentChunkORM.id.in_(stale_ids)))
        return True

    async def index_step(self, session: AsyncSession, step_id: int) -> bool:
        """Перестраивает индекс одного шага по его актуальному содержимому."""
        step = await session.get(StepORM, step_id)
        if step is None:
            return False
        lesson = await session.get(LessonORM, step.lesson_id)
        if lesson is None or lesson.section_id is None:
            return False
        section = await session.get(SectionORM, lesson.section_id)
        if section is None:
            return False
        content = (
            await session.execute(
                select(StepContentORM)
                .where(StepContentORM.step_id == step_id)
                .order_by(StepContentORM.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        text = _clean_text(content.body or "") if content is not None else ""
        old_ids = list(
            (
                await session.execute(
                    select(ContentChunkORM.id).where(ContentChunkORM.step_id == step_id)
                )
            ).scalars()
        )
        if old_ids:
            await session.execute(
                delete(ChunkEmbeddingORM).where(ChunkEmbeddingORM.chunk_id.in_(old_ids))
            )
            await session.execute(delete(ContentChunkORM).where(ContentChunkORM.id.in_(old_ids)))
        source_type = "theory" if step.step_type in ("text", "video") else "task"
        for index, chunk_text in enumerate(self._split_into_chunks(text)):
            chunk = ContentChunkORM(
                course_id=section.course_id,
                lesson_id=lesson.id,
                step_id=step_id,
                chunk_text=chunk_text,
                chunk_index=index,
                source_type=source_type,
            )
            session.add(chunk)
            await session.flush()
            session.add(
                ChunkEmbeddingORM(
                    chunk_id=chunk.id,
                    model_name=self._model_name,
                    embedding=await self._embedder.embed(chunk_text),
                )
            )
        return True

    @staticmethod
    def _split_into_chunks(value: str, size: int = 500, overlap: int = 50) -> list[str]:
        words = value.split()
        if not words:
            return []
        result: list[str] = []
        start = 0
        while start < len(words):
            end = start + size
            result.append(" ".join(words[start:end]))
            if end >= len(words):
                break
            start += size - overlap
        return result
