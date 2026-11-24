## 1. Backend

- [x] 1.1 `domain/models.py`: `ChatSessionSummary`
- [x] 1.2 `application/ports.py`: `ChatRepository.list_sessions(user_id)`; курс у `add_session` и `CourseChunkRepository.search` необязателен
- [x] 1.3 `adapters/persistence/repositories.py`: `list_sessions` с `join courses` и последним сообщением; поиск чанков без фильтра по курсу, когда курс не задан
- [x] 1.4 `application/commands.py` + `application/handlers.py`: `CreateChatSession.course_id` необязателен, ответ по всем курсам для сессии без курса
- [x] 1.5 `entrypoints/api`: схема `SessionListItemRead` + `GET /api/v1/chat/sessions`; `SessionCreate.course_id` необязателен
- [x] 1.6 `tests/fakes.py` + `tests/api/test_api.py` + `tests/unit/test_handlers.py`

## 2. Web

- [x] 2.1 `templates/base.html`: история сессий, сгруппированная по курсам в сворачиваемых `<details>`; без селектора курса
- [x] 2.2 `routers/pages.py`: контекст истории на `/courses` и `/my-courses` (все курсы) и на курсе/шаге (текущий курс)
- [x] 2.3 `static/web.js`: удалить селектор курса, создавать сессию без курса на страницах списка; загрузка/продолжение сессии
- [x] 2.4 `static/web.css`: стили сворачиваемых групп истории
- [x] 2.5 `tests/web/test_web.py`
- [x] 2.6 частичный шаблон `_assistant_history.html` + `GET /assistant/history`: обновление истории при открытии панели и по кнопке «К истории»

## 3. Документация

- [x] 3.1 `README.md`: endpoint `GET /api/v1/chat/sessions`, глобальные вопросы на списках, история по курсам
- [x] 3.2 `AGENTS.md`: заметка об endpoint, истории и глобальном поиске

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate --all --strict`
- [x] 4.2 Пересборка `api`/`web`/`worker`/`scheduler`/`cron`, e2e: история на курсе, глобальный вопрос на списках, сворачиваемые группы
