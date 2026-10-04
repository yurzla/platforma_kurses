from app.rag.context import build_context
from app.rag.query_rewriter import rewrite_question
from app.rag.retrieval import search_course_chunks
from app.rag.service import ask_course, generate_answer_with_history

def print_sources(sources):
    print("\nНАЙДЕННЫЕ ИСТОЧНИКИ:")

    for i, source in enumerate(sources, start=1):
        print(
            f"{i}. chunk_id={source['chunk_id']} | "
            f"distance={source['distance']:.4f} | "
            f"type={source['source_type']} | "
            f"lesson={source['lesson']}"
        )


def test_simple_rag(course_id):
    print("\n" + "=" * 70)
    print("ТЕСТ 1. ОБЫЧНЫЙ RAG")
    print("=" * 70)

    question = "Что такое переменные в Python?"

    print("\nВопрос:")
    print(question)

    result = ask_course(question=question, course_id=course_id)

    print("\nОтвет:")
    print(result["answer"])

    print_sources(result["sources"])

def test_rag_with_history(course_id):
    print("\n" + "=" * 70)
    print("ТЕСТ 2. RAG С ИСТОРИЕЙ")
    print("=" * 70)

    # Имитируем уже состоявшуюся часть диалога
    history = [
        {
            "role": "user",
            "content": "Что такое переменные в Python?",
        },
        {
            "role": "assistant",
            "content": "Переменная в Python - это имя, связанное с некоторым значением.",
        },
    ]

    question = "А какие они бывают?"

    print("\nИсходный вопрос:")
    print(question)

    # 1. Переписываем вопрос для векторного поиска
    rewritten_question = rewrite_question(question=question, history=history)

    print("\nПоисковый запрос:")
    print(rewritten_question)

    # 2. Ищем материалы уже по самостоятельному запросу
    chunks = search_course_chunks(question=rewritten_question, course_id=course_id)

    if not chunks:
        print("\nМатериалы не найдены.")
        return

    print_sources(chunks)

    # 3. Формируем RAG-контекст
    context = build_context(chunks)

    # 4. Для финального ответа используем исходный вопрос, историю разговора и найденный контекст
    answer = generate_answer_with_history(question=question, context=context, history=history)

    print("\nОтвет:")
    print(answer)


if __name__ == "__main__":
    print("=" * 70)
    print("ПРОВЕРКА НОВОГО RAG-МОДУЛЯ")
    print("=" * 70)

    course_id = int(input("Введите course_id для тестирования: "))

    test_simple_rag(course_id)
    test_rag_with_history(course_id)

    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 70)