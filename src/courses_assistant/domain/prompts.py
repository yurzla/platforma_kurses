"""Промпты и подготовка сообщений для LLM (чистые функции)."""

from __future__ import annotations

from collections.abc import Sequence

from courses_assistant.domain.models import ChatMessage, LLMMessage, Role

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


def build_answer_system_prompt(context: str) -> str:
    return f"""
    {SYSTEM_PROMPT}

    МАТЕРИАЛЫ ТЕКУЩЕГО КУРСА:

    {context}
    """.strip()


def build_answer_messages(
    question: str,
    context: str,
    history: Sequence[ChatMessage] | None = None,
) -> list[LLMMessage]:
    messages = [LLMMessage(role=Role.SYSTEM, content=build_answer_system_prompt(context))]

    for message in history or []:
        if message.role in (Role.USER, Role.ASSISTANT):
            messages.append(LLMMessage(role=message.role, content=message.content))

    messages.append(LLMMessage(role=Role.USER, content=question))
    return messages


def history_to_text(history: Sequence[ChatMessage], limit: int = 6) -> str:
    lines: list[str] = []
    for message in list(history)[-limit:]:
        role = "Студент" if message.role == Role.USER else "Ассистент"
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines)


def build_rewrite_prompt(question: str, history: Sequence[ChatMessage]) -> str:
    if not history:
        return question

    return f"""
        Тебе нужно подготовить поисковый запрос для поиска по учебным материалам курса.

        История разговора:
        {history_to_text(history)}

        Новый вопрос студента:
        {question}

        Переформулируй новый вопрос так, чтобы он был понятен
        без истории разговора.

        Правила:
        - сохрани смысл вопроса;
        - раскрой слова вроде "это", "они", "его", "такой";
        - не отвечай на вопрос;
        - не добавляй новую информацию;
        - верни только переформулированный вопрос;
        - если вопрос уже понятен без истории, верни его без изменений.
    """.strip()
