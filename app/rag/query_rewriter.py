# переписывание вопросов
from gigachat.models import Messages, MessagesRole

from app.llm.gigachat import chat_completion


def rewrite_question(question: str, history: list[dict]) -> str:

    if not history:
        return question

    history_text = []

    for message in history[-6:]:
        role = ("Студент" if message["role"] == "user" else "Ассистент")
        history_text.append(f"{role}: {message['content']}")

    history_text = "\n".join(history_text)

    prompt = f"""
        Тебе нужно подготовить поисковый запрос для поиска по учебным материалам курса.

        История разговора:
        {history_text}

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

    messages = [Messages(role=MessagesRole.USER, content=prompt,)]
    rewritten = chat_completion(messages=messages, temperature=0.0)

    return rewritten.strip()