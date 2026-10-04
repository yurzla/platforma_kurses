# RAG-логика
from gigachat.models import Messages, MessagesRole

from app.llm.gigachat import chat_completion
from app.rag.context import build_context
from app.rag.retrieval import search_course_chunks


SYSTEM_PROMPT = """
        Ты - учебный ассистент образовательной платформы.

        Ты отвечаешь студенту на вопросы по текущему курсу.

        Правила:
        1. Используй предоставленные материалы курса.
        2. Учитывай историю разговора, если она передана.
        3. Не придумывай факты, которых нет в материалах курса.
        4. Если материалов недостаточно, прямо скажи об этом.
        5. Объясняй понятно и последовательно.
        6. История разговора нужна для понимания контекста вопроса,
        но не является источником учебных фактов.
    """.strip()


def generate_answer(question: str, context: str) -> str:

    system_prompt = f"""
    {SYSTEM_PROMPT}

    МАТЕРИАЛЫ ТЕКУЩЕГО КУРСА:

    {context}
    """.strip()

    messages = [
        Messages(role=MessagesRole.SYSTEM, content=system_prompt,),
        Messages(role=MessagesRole.USER, content=question,),
    ]

    return chat_completion(messages=messages, temperature=0.2)


def generate_answer_with_history(question: str, context: str, history: list[dict]) -> str:

    system_prompt = f"""
    {SYSTEM_PROMPT}

    МАТЕРИАЛЫ ТЕКУЩЕГО КУРСА:

    {context}
    """.strip()

    messages = [Messages(role=MessagesRole.SYSTEM, content=system_prompt,)]

    for message in history:
        if message["role"] == "user":
            role = MessagesRole.USER

        elif message["role"] == "assistant":
            role = MessagesRole.ASSISTANT

        else:
            continue

        messages.append(Messages(role=role, content=message["content"]))

    messages.append(Messages(role=MessagesRole.USER, content=question))

    return chat_completion(messages=messages, temperature=0.2)


def ask_course(question: str, course_id: int) -> dict:

    chunks = search_course_chunks(question=question, course_id=course_id)

    if not chunks:
        return {"answer": "Материалы курса не найдены.", "sources": []}

    context = build_context(chunks)
    answer = generate_answer(question=question, context=context,)
    
    return {"answer": answer, "sources": chunks}