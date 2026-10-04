import os
import re
import requests
import psycopg

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Настройки
# ─────────────────────────────────────────────

DSN = os.environ.get("DSN")

if not DSN:
    raise RuntimeError("В .env не задан DSN")

OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 768


# ─────────────────────────────────────────────
# Подготовка текста
# ─────────────────────────────────────────────

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_into_chunks(text):
    """
    Разбивает текст примерно по CHUNK_SIZE слов
    с перекрытием CHUNK_OVERLAP.
    """

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE

        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ─────────────────────────────────────────────
# Определение типа контента
# ─────────────────────────────────────────────

def get_source_type(step_type):
    """
    Преобразует тип шага Stepik в тип,
    который используем для RAG.
    """

    if step_type in ("text", "video"):
        return "theory"

    return "task"


# ─────────────────────────────────────────────
# Ollama
# ─────────────────────────────────────────────

def get_embedding(text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    embedding = data["embeddings"][0]

    if len(embedding) != EMBEDDING_DIM:
        raise ValueError(
            f"Ожидалась размерность {EMBEDDING_DIM}, "
            f"получено {len(embedding)}"
        )

    return embedding


def vector_to_pg(vector):
    return "[" + ",".join(map(str, vector)) + "]"


# ─────────────────────────────────────────────
# Проверка / создание embedding
# ─────────────────────────────────────────────

def ensure_embedding(conn, chunk_id, chunk_text):
    """
    Если embedding для chunk уже существует —
    ничего не делаем.

    Если нет — получаем его через Ollama
    и записываем в БД.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT id
            FROM chunk_embeddings
            WHERE chunk_id = %s
              AND model_name = %s
        """, (
            chunk_id,
            EMBEDDING_MODEL
        ))

        existing = cur.fetchone()

    if existing:
        return False

    embedding = get_embedding(chunk_text)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chunk_embeddings (
                chunk_id,
                model_name,
                embedding
            )
            VALUES (%s, %s, %s::vector)
        """, (
            chunk_id,
            EMBEDDING_MODEL,
            vector_to_pg(embedding)
        ))

    return True


# ─────────────────────────────────────────────
# Шаги курса
# ─────────────────────────────────────────────

def process_steps(conn):
    print()
    print("=== Материалы и задания курсов ===")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                sc.step_id,
                sc.body,
                s.lesson_id,
                sec.course_id,
                s.step_type
            FROM step_contents sc
            JOIN steps s
                ON s.id = sc.step_id
            JOIN lessons l
                ON l.id = s.lesson_id
            JOIN sections sec
                ON sec.id = l.section_id
            WHERE sc.body IS NOT NULL
              AND TRIM(sc.body) <> ''
            ORDER BY sc.step_id
        """)

        rows = cur.fetchall()

    print(f"Найдено текстовых шагов: {len(rows)}")

    new_chunks = 0
    new_embeddings = 0
    existing_embeddings = 0

    for number, row in enumerate(rows, start=1):

        step_id, body, lesson_id, course_id, step_type = row

        text = clean_text(body)

        if not text:
            continue

        source_type = get_source_type(step_type)
        chunks = split_into_chunks(text)

        print(
            f"[{number}/{len(rows)}] "
            f"step_id={step_id}, "
            f"type={step_type}, "
            f"source={source_type}, "
            f"chunks={len(chunks)}"
        )

        for chunk_index, chunk_text in enumerate(chunks):

            # ─────────────────────────────────────
            # Ищем существующий chunk
            # ─────────────────────────────────────

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, source_type
                    FROM content_chunks
                    WHERE step_id = %s
                      AND chunk_index = %s
                """, (
                    step_id,
                    chunk_index
                ))

                existing_chunk = cur.fetchone()

            if existing_chunk:
                chunk_id = existing_chunk[0]

                # Исправляем source_type у старых записей.
                if existing_chunk[1] != source_type:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE content_chunks
                            SET source_type = %s
                            WHERE id = %s
                        """, (
                            source_type,
                            chunk_id
                        ))

            else:
                # ─────────────────────────────────
                # Chunk ещё не существует
                # ─────────────────────────────────

                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO content_chunks (
                            course_id,
                            lesson_id,
                            step_id,
                            chunk_text,
                            chunk_index,
                            source_type
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        course_id,
                        lesson_id,
                        step_id,
                        chunk_text,
                        chunk_index,
                        source_type
                    ))

                    chunk_id = cur.fetchone()[0]

                new_chunks += 1

            # ─────────────────────────────────────
            # ВАЖНО:
            # embedding создаём только если его нет
            # ─────────────────────────────────────

            created = ensure_embedding(
                conn,
                chunk_id,
                chunk_text
            )

            if created:
                new_embeddings += 1
                print(
                    f"    chunk {chunk_index}: "
                    f"embedding создан ({EMBEDDING_DIM} dim)"
                )
            else:
                existing_embeddings += 1
                print(
                    f"    chunk {chunk_index}: "
                    f"embedding уже есть"
                )

            conn.commit()

    return new_chunks, new_embeddings, existing_embeddings


# ─────────────────────────────────────────────
# Описания курсов
# ─────────────────────────────────────────────

def process_course_descriptions(conn):
    print()
    print("=== Описания курсов ===")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                id,
                title,
                description
            FROM courses
            WHERE description IS NOT NULL
              AND TRIM(description) <> ''
            ORDER BY id
        """)

        courses = cur.fetchall()

    print(f"Найдено описаний курсов: {len(courses)}")

    new_chunks = 0
    new_embeddings = 0
    existing_embeddings = 0

    for number, (course_id, title, description) in enumerate(
        courses,
        start=1
    ):

        # Добавляем название курса к описанию.
        # Для смыслового поиска это полезно.
        text = clean_text(
            f"{title}. {description}"
        )

        chunks = split_into_chunks(text)

        print(
            f"[{number}/{len(courses)}] "
            f"course_id={course_id}, "
            f"chunks={len(chunks)}"
        )

        for chunk_index, chunk_text in enumerate(chunks):

            # У описания курса:
            # lesson_id = NULL
            # step_id = NULL
            #
            # Поэтому ищем по course_id + source_type + chunk_index.

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id
                    FROM content_chunks
                    WHERE course_id = %s
                      AND lesson_id IS NULL
                      AND step_id IS NULL
                      AND source_type = 'course_description'
                      AND chunk_index = %s
                """, (
                    course_id,
                    chunk_index
                ))

                existing_chunk = cur.fetchone()

            if existing_chunk:
                chunk_id = existing_chunk[0]

            else:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO content_chunks (
                            course_id,
                            lesson_id,
                            step_id,
                            chunk_text,
                            chunk_index,
                            source_type
                        )
                        VALUES (
                            %s,
                            NULL,
                            NULL,
                            %s,
                            %s,
                            'course_description'
                        )
                        RETURNING id
                    """, (
                        course_id,
                        chunk_text,
                        chunk_index
                    ))

                    chunk_id = cur.fetchone()[0]

                new_chunks += 1

            # Снова: embedding только если его нет.
            created = ensure_embedding(
                conn,
                chunk_id,
                chunk_text
            )

            if created:
                new_embeddings += 1

                print(
                    f"    chunk {chunk_index}: "
                    f"embedding создан ({EMBEDDING_DIM} dim)"
                )
            else:
                existing_embeddings += 1

                print(
                    f"    chunk {chunk_index}: "
                    f"embedding уже есть"
                )

            conn.commit()

    return new_chunks, new_embeddings, existing_embeddings


# ─────────────────────────────────────────────
# Итоговая проверка
# ─────────────────────────────────────────────

def print_statistics(conn):
    print()
    print("=== Итоговая статистика ===")

    with conn.cursor() as cur:

        cur.execute("""
            SELECT COUNT(*)
            FROM content_chunks
        """)
        chunks_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM chunk_embeddings
            WHERE model_name = %s
        """, (EMBEDDING_MODEL,))
        embeddings_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM content_chunks cc
            WHERE NOT EXISTS (
                SELECT 1
                FROM chunk_embeddings ce
                WHERE ce.chunk_id = cc.id
                  AND ce.model_name = %s
            )
        """, (EMBEDDING_MODEL,))
        missing_embeddings = cur.fetchone()[0]

        cur.execute("""
            SELECT source_type, COUNT(*)
            FROM content_chunks
            GROUP BY source_type
            ORDER BY source_type
        """)

        source_stats = cur.fetchall()

    print(f"Всего chunks: {chunks_count}")
    print(f"Всего embeddings: {embeddings_count}")
    print(f"Chunks без embedding: {missing_embeddings}")

    print()
    print("По типам:")

    for source_type, count in source_stats:
        print(f"  {source_type}: {count}")


# ─────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────

def main():

    with psycopg.connect(DSN) as conn:

        step_stats = process_steps(conn)
        course_stats = process_course_descriptions(conn)

        print_statistics(conn)

    print()
    print("Готово.")

    print(
        "Шаги: "
        f"новых chunks={step_stats[0]}, "
        f"новых embeddings={step_stats[1]}, "
        f"уже существовало={step_stats[2]}"
    )

    print(
        "Описания курсов: "
        f"новых chunks={course_stats[0]}, "
        f"новых embeddings={course_stats[1]}, "
        f"уже существовало={course_stats[2]}"
    )


if __name__ == "__main__":
    main()