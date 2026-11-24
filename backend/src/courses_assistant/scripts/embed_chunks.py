"""Чанкинг материалов курса и создание эмбеддингов (Ollama nomic-embed-text).

Пример: python -m courses_assistant.scripts.embed_chunks
"""

from __future__ import annotations

import asyncio

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.adapters.embeddings.ollama import OllamaEmbedder
from courses_assistant.config import get_settings
from courses_assistant.scripts.load_stepik import clean_text

app = typer.Typer(help="Чанкинг и эмбеддинги материалов курса.")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def split_into_chunks(value: str) -> list[str]:
    words = value.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def get_source_type(step_type: str) -> str:
    return "theory" if step_type in ("text", "video") else "task"


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(map(str, embedding)) + "]"


async def _ensure_embedding(
    conn: AsyncConnection, embedder: OllamaEmbedder, model: str, chunk_id: int, chunk_text: str
) -> bool:
    existing = await conn.execute(
        text(
            "SELECT ce.id, cc.chunk_text FROM chunk_embeddings ce "
            "JOIN content_chunks cc ON cc.id = ce.chunk_id "
            "WHERE ce.chunk_id = :chunk_id AND ce.model_name = :model"
        ),
        {"chunk_id": chunk_id, "model": model},
    )
    row = existing.first()
    if row and row[1] == chunk_text:
        return False
    if row:
        await conn.execute(
            text("DELETE FROM chunk_embeddings WHERE id = :id"), {"id": row[0]}
        )

    embedding = await embedder.embed(chunk_text)
    await conn.execute(
        text(
            "INSERT INTO chunk_embeddings (chunk_id, model_name, embedding) "
            "VALUES (:chunk_id, :model, CAST(:embedding AS vector))"
        ),
        {"chunk_id": chunk_id, "model": model, "embedding": _vector_literal(embedding)},
    )
    return True


async def _upsert_chunk(
    conn: AsyncConnection,
    *,
    course_id: int,
    lesson_id: int | None,
    step_id: int | None,
    chunk_text: str,
    chunk_index: int,
    source_type: str,
) -> tuple[int, bool]:
    if step_id is not None:
        existing = await conn.execute(
            text(
                "SELECT id, source_type FROM content_chunks "
                "WHERE step_id = :step_id AND chunk_index = :chunk_index"
            ),
            {"step_id": step_id, "chunk_index": chunk_index},
        )
        row = existing.first()
        if row:
            if row[1] != source_type:
                await conn.execute(
                    text("UPDATE content_chunks SET source_type = :st WHERE id = :id"),
                    {"st": source_type, "id": row[0]},
                )
            return int(row[0]), False
    else:
        existing = await conn.execute(
            text(
                "SELECT id FROM content_chunks "
                "WHERE course_id = :course_id AND lesson_id IS NULL AND step_id IS NULL "
                "AND source_type = :source_type AND chunk_index = :chunk_index"
            ),
            {
                "course_id": course_id,
                "source_type": source_type,
                "chunk_index": chunk_index,
            },
        )
        row = existing.first()
        if row:
            await conn.execute(
                text("UPDATE content_chunks SET chunk_text = :chunk_text WHERE id = :id"),
                {"chunk_text": chunk_text, "id": row[0]},
            )
            return int(row[0]), False

    inserted = await conn.execute(
        text(
            """
            INSERT INTO content_chunks
                (course_id, lesson_id, step_id, chunk_text, chunk_index, source_type)
            VALUES (:course_id, :lesson_id, :step_id, :chunk_text, :chunk_index, :source_type)
            RETURNING id
            """
        ),
        {
            "course_id": course_id,
            "lesson_id": lesson_id,
            "step_id": step_id,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index,
            "source_type": source_type,
        },
    )
    return int(inserted.scalar_one()), True


async def _run(rebuild: bool = False) -> None:
    settings = get_settings()
    embedder = OllamaEmbedder(
        url=settings.ollama_url,
        model=settings.embedding_model,
        dimension=settings.embedding_dimension,
    )
    engine = create_async_engine(settings.database_url)

    new_chunks = 0
    new_embeddings = 0
    try:
        async with engine.connect() as conn:
            if rebuild:
                await conn.execute(text("TRUNCATE content_chunks RESTART IDENTITY CASCADE"))
                await conn.commit()
                typer.echo("Существующие чанки и эмбеддинги удалены (--rebuild).")
            rows = (
                await conn.execute(
                    text(
                        """
                        SELECT sc.step_id, sc.body, s.lesson_id, sec.course_id, s.step_type
                        FROM step_contents sc
                        JOIN steps s ON s.id = sc.step_id
                        JOIN lessons l ON l.id = s.lesson_id
                        JOIN sections sec ON sec.id = l.section_id
                        WHERE sc.body IS NOT NULL AND TRIM(sc.body) <> ''
                        ORDER BY sc.step_id
                        """
                    )
                )
            ).all()

            typer.echo(f"Найдено текстовых шагов: {len(rows)}")
            for number, row in enumerate(rows, start=1):
                step_id, body, lesson_id, course_id, step_type = row
                text_value = clean_text(body)
                if not text_value:
                    continue
                source_type = get_source_type(step_type)
                chunks = split_into_chunks(text_value)
                typer.echo(
                    f"[{number}/{len(rows)}] step_id={step_id}, chunks={len(chunks)}"
                )
                for chunk_index, chunk_text in enumerate(chunks):
                    chunk_id, created = await _upsert_chunk(
                        conn,
                        course_id=course_id,
                        lesson_id=lesson_id,
                        step_id=step_id,
                        chunk_text=chunk_text,
                        chunk_index=chunk_index,
                        source_type=source_type,
                    )
                    new_chunks += int(created)
                    if await _ensure_embedding(
                        conn, embedder, settings.embedding_model, chunk_id, chunk_text
                    ):
                        new_embeddings += 1
                    await conn.commit()

            courses = (
                await conn.execute(
                    text(
                        "SELECT id, title, description FROM courses "
                        "WHERE description IS NOT NULL AND TRIM(description) <> '' ORDER BY id"
                    )
                )
            ).all()

            typer.echo(f"Найдено описаний курсов: {len(courses)}")
            for course_id, title, description in courses:
                chunks = split_into_chunks(clean_text(f"{title}. {description}"))
                for chunk_index, chunk_text in enumerate(chunks):
                    chunk_id, created = await _upsert_chunk(
                        conn,
                        course_id=course_id,
                        lesson_id=None,
                        step_id=None,
                        chunk_text=chunk_text,
                        chunk_index=chunk_index,
                        source_type="course_description",
                    )
                    new_chunks += int(created)
                    if await _ensure_embedding(
                        conn, embedder, settings.embedding_model, chunk_id, chunk_text
                    ):
                        new_embeddings += 1
                    await conn.commit()
    finally:
        await engine.dispose()

    typer.echo(f"Готово. Новых chunks={new_chunks}, новых embeddings={new_embeddings}.")


@app.command()
def main(
    rebuild: bool = typer.Option(
        False, "--rebuild", help="Удалить существующие чанки и эмбеддинги и построить заново."
    ),
) -> None:
    asyncio.run(_run(rebuild=rebuild))


if __name__ == "__main__":
    app()
