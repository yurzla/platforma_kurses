from gigachat.models import Messages, MessagesRole

from app.core.database import get_connection
from app.embeddings.client import get_embedding
from app.embeddings.vector_utils import vector_to_pg
from app.llm.gigachat import chat_completion


def test_database():
    print("\n=== 1. PostgreSQL ===")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]

    print("OK")
    print(version)


def test_embeddings():
    print("\n=== 2. Ollama / Embeddings ===")
    embedding = get_embedding("Что такое переменные в Python?")

    print("OK")
    print("Размерность:", len(embedding))
    print("Первые 5 значений:", embedding[:5])

    pg_vector = vector_to_pg(embedding)

    print("Формат для PostgreSQL:")
    print(pg_vector[:100] + "...")


def test_gigachat():
    print("\n=== 3. GigaChat ===")

    messages = [
        Messages(
            role=MessagesRole.USER,
            content=("Ответь одним коротким предложением: что такое Python?"),
        )
    ]

    answer = chat_completion(messages=messages, temperature=0.0)

    print("OK")
    print("Ответ:", answer)


if __name__ == "__main__":
    print("=" * 60)
    print("ПРОВЕРКА ИНФРАСТРУКТУРЫ")
    print("=" * 60)

    try:
        test_database()
        test_embeddings()
        test_gigachat()

    except Exception as error:
        print("\nОШИБКА:")
        print(type(error).__name__)
        print(error)

        raise

    print("\n" + "=" * 60)
    print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("=" * 60)