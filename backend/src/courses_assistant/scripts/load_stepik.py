"""Загрузка JSON-дампа Stepik в PostgreSQL.

Пример: python -m courses_assistant.scripts.load_stepik --dump-dir stepik_dump
"""

from __future__ import annotations

import asyncio
import html
import json
import re
from pathlib import Path

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from courses_assistant.config import get_settings
from courses_assistant.scripts.renumber_steps import renumber_step_positions

app = typer.Typer(help="Загрузка дампа Stepik в БД.")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


_BLOCK_BREAK = re.compile(
    r"<\s*/?\s*(?:p|div|br|li|ul|ol|h[1-6]|tr|table|blockquote|section)\b[^>]*>",
    re.IGNORECASE,
)


def clean_description(value: str | None) -> str:
    """Убирает разметку, но сохраняет абзацы и переносы строк описания."""
    if not value:
        return ""
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLOCK_BREAK.sub("\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    lines = [re.sub(r"[ \t\f\v]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_empty_step(block: dict) -> bool:
    """Шаг пустой, если у него нет текстового содержимого."""
    body = block.get("text")
    return not body or not body.strip()


async def load_course(conn: AsyncConnection, data: dict) -> None:
    course = data["course"]
    ext_course_id = course["id"]

    result = await conn.execute(
        text(
            """
            INSERT INTO courses (external_id, title, description, language, is_published)
            VALUES (:ext, :title, :description, :language, true)
            ON CONFLICT (external_id) DO UPDATE
                SET title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    language = EXCLUDED.language
            RETURNING id
            """
        ),
        {
            "ext": ext_course_id,
            "title": course["title"],
            "description": clean_description(
                course.get("description") or course.get("summary")
            ),
            "language": course.get("language", "ru"),
        },
    )
    course_db_id = result.scalar_one()

    section_ext_to_db: dict[int, int] = {}
    for position, section_ext in enumerate(course.get("sections", []), start=1):
        res = await conn.execute(
            text(
                "INSERT INTO sections (course_id, position, title) "
                "VALUES (:course_id, :position, :title) RETURNING id"
            ),
            {"course_id": course_db_id, "position": position, "title": f"Модуль {position}"},
        )
        section_ext_to_db[section_ext] = res.scalar_one()

    lesson_ext_to_db: dict[int, int] = {}
    for unit in data.get("units", []):
        lesson_ext = unit["lesson"]
        if lesson_ext in lesson_ext_to_db:
            continue
        lesson = data["lessons"].get(str(lesson_ext), {})
        res = await conn.execute(
            text(
                """
                INSERT INTO lessons (external_id, section_id, title, position)
                VALUES (:ext, :section_id, :title, :position)
                ON CONFLICT (external_id) DO UPDATE
                    SET title = EXCLUDED.title,
                        section_id = EXCLUDED.section_id,
                        position = EXCLUDED.position
                RETURNING id
                """
            ),
            {
                "ext": lesson_ext,
                "section_id": section_ext_to_db.get(unit["section"]),
                "title": lesson.get("title", f"Урок {lesson_ext}"),
                "position": unit.get("position", 0),
            },
        )
        lesson_ext_to_db[lesson_ext] = res.scalar_one()

    steps_count = 0
    skipped_empty = 0
    for ext_step_id, step in data["steps"].items():
        lesson_db = lesson_ext_to_db.get(step["lesson"])
        if not lesson_db:
            typer.echo(f"  ! step {ext_step_id}: lesson {step['lesson']} не найден")
            continue
        block = step["block"]
        body = block.get("text")
        if is_empty_step(block):
            skipped_empty += 1
            continue
        res = await conn.execute(
            text(
                """
                INSERT INTO steps (external_id, lesson_id, position, step_type, is_enabled)
                VALUES (:ext, :lesson_id, :position, :step_type, true)
                ON CONFLICT (external_id) DO UPDATE
                    SET lesson_id = EXCLUDED.lesson_id,
                        position = EXCLUDED.position,
                        step_type = EXCLUDED.step_type
                RETURNING id
                """
            ),
            {
                "ext": int(ext_step_id),
                "lesson_id": lesson_db,
                "position": step["position"],
                "step_type": block["name"],
            },
        )
        step_db = res.scalar_one()
        options = {k: v for k, v in block.items() if k not in ("text", "name")}
        await conn.execute(
            text(
                "INSERT INTO step_contents (step_id, content_type, body, options) "
                "VALUES (:step_id, 'html', :body, CAST(:options AS jsonb))"
            ),
            {"step_id": step_db, "body": body, "options": json.dumps(options)},
        )
        steps_count += 1

    await renumber_step_positions(conn, course_db_id)
    await conn.commit()
    typer.echo(
        f"OK course {ext_course_id}: {course['title']} | "
        f"секций {len(section_ext_to_db)}, уроков {len(lesson_ext_to_db)}, "
        f"шагов {steps_count}, пустых пропущено {skipped_empty}"
    )


async def _run(dump_dir: Path) -> None:
    settings = get_settings()
    files = sorted(dump_dir.glob("course_*.json"))
    if not files:
        raise typer.BadParameter(f"Нет файлов {dump_dir}/course_*.json")
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.begin() as conn:
            for path in files:
                typer.echo(f"-> {path}")
                data = json.loads(path.read_text(encoding="utf-8"))
                await load_course(conn, data)
    finally:
        await engine.dispose()


@app.command()
def main(dump_dir: Path = typer.Option(Path("stepik_dump"), "--dump-dir", "-d")) -> None:
    asyncio.run(_run(dump_dir))


if __name__ == "__main__":
    app()
