# Tasks

## 1. API удаления и выгрузки диалогов

- [x] 1.1 Вернуть в `backend/pyproject.toml` зависимость `fpdf2>=2.7.4` и проверить `uv lock --check`
- [x] 1.2 Вернуть в `routers/chat.py` `DELETE /sessions`, `DELETE /sessions/{id}` и `GET /sessions/{id}/export`; проверить `uv run pytest tests/api/test_chat_delete_export.py tests/unit/test_chat_export.py`

## 2. Страница шага: навигация и прогресс

- [x] 2.1 Вернуть в `client.py` подстановку `merged_cookie` при вызове API; проверить `tests/web/test_web_steps.py::test_step_page_uses_refreshed_token_for_course_structure`
- [x] 2.2 Вернуть в `pages.py` `_step_neighbours`, `_step_markers`, `_step_context` и контекст шаблона; убрать `_next_step_url`
- [x] 2.3 Восстановить `step.html`: крошки, типы шагов, прогресс-бар, навигацию и состояние «Выполнено»
- [x] 2.4 Восстановить в `web.js` `updateStepProgress` и переключение кнопки завершения, сохранив текущие тексты результата
- [x] 2.5 Вернуть в `web.css` стили прогресс-бара, точек, навигации и `.btn.done`; проверить `uv run pytest tests/web/test_web_steps.py`

## 3. Web-управление чатами

- [x] 3.1 Вернуть в `base.html` контейнер экспорта и модалку подтверждения
- [x] 3.2 Вернуть в `_assistant_history.html` удаление диалога и «Очистить историю»
- [x] 3.3 Объединить в `web.js` экспорт, удаление, очистку и модалку с текущим форматированием ответов
- [x] 3.4 Вернуть в `web.css` стили истории, корзины, модалки и `chat-actions`, не ломая `.btn.danger` преподавателя; проверить `uv run pytest tests/web/test_web_chat.py`

## 4. Интеграционная проверка

- [x] 4.1 Прогнать `make lint`, `make typecheck` и `make test-unit`
- [x] 4.2 Проверить `openspec validate restore-step-and-chat-controls --strict`

## Workflow follow-up

- Заархивировать change после успешной проверки.
