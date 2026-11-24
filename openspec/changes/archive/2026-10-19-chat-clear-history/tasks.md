## 1. Backend

- [x] 1.1 `ports.py`: `ChatRepository.list_session_ids`/`delete_sessions`,
      `JobRepository.delete_by_sessions`
- [x] 1.2 `adapters/persistence/repositories.py`: SQL-реализации (сначала jobs, затем сессии)
- [x] 1.3 `entrypoints/api/routers/chat.py`: `DELETE /api/v1/chat/sessions?course_id=`
- [x] 1.4 `tests/fakes.py`: реализации новых методов в фейках

## 2. Web

- [x] 2.1 `_assistant_history.html`: кнопка «Очистить историю» при непустой истории
- [x] 2.2 `web.js`: подтверждение, DELETE через прокси с `course_id`, перезагрузка истории, ошибки
- [x] 2.3 `web.css`: кнопка удаления 40 px и иконка 18 px, стиль кнопки очистки

## 3. Tests

- [x] 3.1 API: очистка всех сессий, фильтр по курсу, чужие сессии не трогаются, 401
- [x] 3.2 Web: кнопка очистки и проксирование DELETE, пустое состояние после очистки

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate chat-clear-history --strict`
- [x] 4.3 Пересобрать `api` и `web`, проверить очистку в UI
