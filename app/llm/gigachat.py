# должен просто уметь отправить уже подготовленные сообщения в GigaChat
from gigachat import GigaChat
from gigachat.models import Chat
from app.core.config import GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_BASE_URL, GIGACHAT_MODEL

def chat_completion(messages, temperature: float = 0.2) -> str:

    if not GIGACHAT_CREDENTIALS:
        raise RuntimeError("Не задан GIGACHAT_CREDENTIALS.")

    with GigaChat(
        credentials=GIGACHAT_CREDENTIALS, 
        scope=GIGACHAT_SCOPE,
        base_url=GIGACHAT_BASE_URL,
        verify_ssl_certs=False,
        timeout=120,
    ) as client:

        chat = Chat(
            model=GIGACHAT_MODEL,
            messages=messages,
            temperature=temperature,
        )

        response = client.chat(chat)

    return response.choices[0].message.content