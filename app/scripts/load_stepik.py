import json, glob, os, psycopg
from psycopg.types.json import Jsonb

DSN = os.environ.get("DSN", "postgresql://postgres:postgres@localhost:5432/edu_platform_kurses")
DUMP_DIR = "stepik_dump"

def clean_text(s):
    """Убираем HTML-теги на грубом уровне, чтобы chunk'и не были мусором."""
    if not s:
        return ""
    import re
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def load_course(conn, data):
    course = data["course"]
    ext_course_id = course["id"]
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO courses (external_id, title, description, language, is_published)
        VALUES (%s, %s, %s, %s, true)
        ON CONFLICT (external_id) DO UPDATE
            SET title = EXCLUDED.title,
                description = EXCLUDED.description,
                language = EXCLUDED.language
        RETURNING id
    """, (
        ext_course_id,
        course["title"],
        clean_text(course.get("description") or course.get("summary")),
        course.get("language", "ru"),
    ))
    course_db_id = cur.fetchone()[0]

    # ── секции ────────────────────────────────────────────────
    # В JSON курса приходит список id секций (int), без названий.
    # Названия секций лежат в /api/sections, но в вашем дампе их нет.
    # Поэтому используем "Модуль N" как заголовок.
    section_ids = course.get("sections", [])
    section_ext_to_db = {}
    for pos, sec_ext in enumerate(section_ids, start=1):
        cur.execute("""
            INSERT INTO sections (course_id, position, title)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (course_db_id, pos, f"Модуль {pos}"))
        section_ext_to_db[sec_ext] = cur.fetchone()[0]

    # ── уроки ─────────────────────────────────────────────────
    # units[] даёт связку section ↔ lesson; по ней и определим section_id.
    lesson_ext_to_db = {}
    for u in data.get("units", []):
        lesson_ext = u["lesson"]
        if lesson_ext in lesson_ext_to_db:
            continue
        section_db = section_ext_to_db.get(u["section"])
        l = data["lessons"].get(str(lesson_ext), {})
        cur.execute("""
            INSERT INTO lessons (external_id, section_id, title, position)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (external_id) DO UPDATE
                SET title = EXCLUDED.title,
                    section_id = EXCLUDED.section_id,
                    position = EXCLUDED.position
            RETURNING id
        """, (
            lesson_ext,
            section_db,
            l.get("title", f"Урок {lesson_ext}"),
            u.get("position", 0),
        ))
        lesson_ext_to_db[lesson_ext] = cur.fetchone()[0]

    # ── шаги + step_contents ──────────────────────────────────
    steps_count = 0
    for ext_step_id_str, s in data["steps"].items():
        lesson_db = lesson_ext_to_db.get(s["lesson"])
        if not lesson_db:
            print(f"  ! step {ext_step_id_str}: lesson {s['lesson']} не найден")
            continue
        block = s["block"]
        step_type = block["name"]

        cur.execute("""
            INSERT INTO steps (external_id, lesson_id, position, step_type, is_enabled)
            VALUES (%s, %s, %s, %s, true)
            ON CONFLICT (external_id) DO UPDATE
                SET lesson_id = EXCLUDED.lesson_id,
                    position  = EXCLUDED.position,
                    step_type = EXCLUDED.step_type
            RETURNING id
        """, (int(ext_step_id_str), lesson_db, s["position"], step_type))
        step_db = cur.fetchone()[0]

        # options = всё, кроме text и name (video, samples, code_templates, limits, ...)
        options = {k: v for k, v in block.items() if k not in ("text", "name")}
        cur.execute("""
            INSERT INTO step_contents (step_id, content_type, body, options)
            VALUES (%s, 'html', %s, %s)
        """, (step_db, block.get("text"), Jsonb(options)))
        steps_count += 1

    conn.commit()
    print(f"OK course {ext_course_id}: {course['title']} | "
          f"секций {len(section_ext_to_db)}, уроков {len(lesson_ext_to_db)}, шагов {steps_count}")

if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(DUMP_DIR, "course_*.json")))
    if not files:
        raise SystemExit(f"Нет файлов в {DUMP_DIR}/course_*.json")
    with psycopg.connect(DSN) as conn:
        for path in files:
            print(f"→ {path}")
            with open(path, encoding="utf-8") as f:
                load_course(conn, json.load(f))