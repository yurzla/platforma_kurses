# работа с таблицами чата
import json
from app.core.database import get_connection

def create_chat_session(user_id: int, course_id: int) -> int:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO chat_sessions (user_id, course_id)
                    VALUES (%s, %s)
                    RETURNING id
                """,
                (user_id, course_id),
            )

            session_id = cur.fetchone()[0]

    return session_id

def save_message(session_id: int, role: str, content: str, used_chunk_ids: list[int] | None = None) -> int:

    if role not in ("user", "assistant"):
        raise ValueError("role должен быть 'user' или 'assistant'")

    used_chunk_ids_json = (json.dumps(used_chunk_ids) if used_chunk_ids is not None else None)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO chat_messages (session_id, role, content, used_chunk_ids)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """,
                (session_id, role, content, used_chunk_ids_json,),
            )

            message_id = cur.fetchone()[0]

    return message_id

def get_chat_history(session_id: int, limit: int = 10) -> list[dict]:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT
                        role,
                        content,
                        created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                """,
                (session_id, limit,),
            )

            rows = cur.fetchall()

    rows.reverse()

    return [
        {"role": row[0], "content": row[1], "created_at": row[2],}
        for row in rows
    ]


def get_session(session_id: int) -> dict | None:

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT
                        id,
                        user_id,
                        course_id,
                        started_at
                    FROM chat_sessions
                    WHERE id = %s
                """,
                (session_id,),
            )

            row = cur.fetchone()

    if row is None:
        return None

    return {"id": row[0], "user_id": row[1], "course_id": row[2], "created_at": row[3]}