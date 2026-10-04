from app.chat.repository import (get_session, get_chat_history, save_message)

from app.rag.context import build_context
from app.rag.query_rewriter import rewrite_question
from app.rag.retrieval import search_course_chunks
from app.rag.service import generate_answer_with_history


def send_message(session_id: int, question: str) -> dict:

    # 1. Получаем информацию о сессии
    session = get_session(session_id)

    if session is None:
        raise ValueError(f"Чат-сессия {session_id} не найдена.")
    course_id = session["course_id"]

    # 2. Получаем историю до сохранения текущего сообщения.
    history = get_chat_history(session_id=session_id, limit=10)

    # 3. Делаем вопрос самостоятельным для семантического поиска.
    rewritten_question = rewrite_question(question=question, history=history)

    # 4. Сохраняем именно оригинальный вопрос пользователя.
    save_message(session_id=session_id, role="user", content=question)

    # 5. Ищем релевантные материалы курса.
    chunks = search_course_chunks(question=rewritten_question, course_id=course_id)

    # 6. Если материалов нет, не отправляем пустой контекст в LLM.
    if not chunks:
        answer = ("Не удалось найти подходящие материалы в текущем курсе.")

        save_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            used_chunk_ids=[],
        )

        return {"answer": answer, "sources": [], "rewritten_question": rewritten_question}

    # 7. Собираем контекст.
    context = build_context(chunks)

    # 8. Генерируем ответ.
    # В LLM передаём оригинальный вопрос, а не rewritten_question.
    # rewritten_question нужен только для поиска.

    answer = generate_answer_with_history(
        question=question,
        context=context,
        history=history,
    )

    # 9. Запоминаем, какие chunks использовались при генерации.
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    # 10. Сохраняем ответ ассистента.
    save_message(
        session_id=session_id,
        role="assistant",
        content=answer,
        used_chunk_ids=chunk_ids,
    )

    # 11. Возвращаем результат.
    return {"answer": answer, "sources": chunks, "rewritten_question": rewritten_question}