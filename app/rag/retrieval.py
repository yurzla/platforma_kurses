# поиск материалов курса
from app.core.config import EMBEDDING_MODEL
from app.core.database import get_connection
from app.embeddings.client import get_embedding
from app.embeddings.vector_utils import vector_to_pg

TOP_K = 5

def search_course_chunks(question: str, course_id: int, limit: int = TOP_K) -> list[dict]:

    query_embedding = get_embedding(question)
    vector = vector_to_pg(query_embedding)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT
                        cc.id,
                        cc.chunk_text,
                        cc.source_type,
                        l.title AS lesson_title,
                        ce.embedding <=> %s::vector AS distance
                    FROM chunk_embeddings ce

                    JOIN content_chunks cc ON cc.id = ce.chunk_id
                    LEFT JOIN lessons l ON l.id = cc.lesson_id
                    WHERE cc.course_id = %s AND ce.model_name = %s AND cc.source_type IN ('theory', 'task')
                    ORDER BY ce.embedding <=> %s::vector
                    LIMIT %s
                """,
                (vector, course_id, EMBEDDING_MODEL, vector, limit,),
            )
            rows = cur.fetchall()

    return [
        {
            "chunk_id": row[0],
            "text": row[1],
            "source_type": row[2],
            "lesson": row[3],
            "distance": float(row[4]),
        }
        for row in rows
    ]