from app.chat.repository import create_chat_session, get_chat_history, get_session
from app.chat.service import send_message

def print_sources(sources):
    print("\nИсточники:")

    if not sources:
        print("  Нет источников")
        return

    for i, source in enumerate(sources, start=1):
        print(
            f"  {i}. "
            f"chunk_id={source['chunk_id']} | "
            f"distance={source['distance']:.4f} | "
            f"type={source['source_type']} | "
            f"lesson={source['lesson']}"
        )

def print_result(result):
    print("\nПоисковый запрос:")
    print(result["rewritten_question"])

    print("\nОтвет:")
    print(result["answer"])

    print_sources(result["sources"])


def test_chat(user_id: int, course_id: int):
    print("\n" + "=" * 70)
    print("1. СОЗДАНИЕ ЧАТ-СЕССИИ")
    print("=" * 70)

    session_id = create_chat_session(user_id=user_id, course_id=course_id)

    print(f"Создана сессия: {session_id}")

    session = get_session(session_id)

    print("Данные сессии:")
    print(session)

    # Первый вопрос
    print("\n" + "=" * 70)
    print("2. ПЕРВЫЙ ВОПРОС")
    print("=" * 70)

    question_1 = "Что такое переменные в Python?"

    print("\nПользователь:")
    print(question_1)

    result_1 = send_message(session_id=session_id, question=question_1)

    print_result(result_1)

    # Второй вопрос
    print("\n" + "=" * 70)
    print("3. ВОПРОС С УЧЁТОМ ИСТОРИИ")
    print("=" * 70)

    question_2 = "А какие они бывают?"

    print("\nПользователь:")
    print(question_2)

    result_2 = send_message(session_id=session_id, question=question_2)

    print_result(result_2)

    # Проверяем историю в БД
    print("\n" + "=" * 70)
    print("4. ИСТОРИЯ ЧАТА ИЗ БД")
    print("=" * 70)

    history = get_chat_history(session_id=session_id, limit=20)

    for i, message in enumerate(history, start=1):
        print(f"\n{i}. [{message['role']}] {message['created_at']}")
        print(message["content"])

    # Финальные проверки
    print("\n" + "=" * 70)
    print("5. ПРОВЕРКИ")
    print("=" * 70)

    assert len(history) == 4, (f"Ожидалось 4 сообщения, получено {len(history)}")
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[3]["role"] == "assistant"

    assert history[0]["content"] == question_1
    assert history[2]["content"] == question_2

    assert result_1["answer"]
    assert result_2["answer"]

    assert result_1["sources"]
    assert result_2["sources"]

    print("OK: сессия создана")
    print("OK: первый вопрос обработан")
    print("OK: второй вопрос обработан")
    print("OK: сообщения сохранены в БД")
    print("OK: порядок сообщений правильный")
    print("OK: RAG вернул источники")

    print("\n" + "=" * 70)
    print("ТЕСТ ЧАТА УСПЕШНО ЗАВЕРШЁН")
    print("=" * 70)


if __name__ == "__main__":
    print("=" * 70)
    print("ПРОВЕРКА CHAT-МОДУЛЯ")
    print("=" * 70)

    user_id = int(input("Введите user_id тестового студента: "))
    course_id = int(input("Введите course_id курса: "))

    test_chat(user_id=user_id, course_id=course_id)