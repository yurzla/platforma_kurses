## 1. Промпт и генерация

- [x] 1.1 `domain/prompts.py`: `current_course` в `build_answer_system_prompt`/`build_answer_messages`, секция «ТЕКУЩИЙ КУРС СТУДЕНТА»
- [x] 1.2 `application/rag.py`: `generate_answer(current_course=...)`
- [x] 1.3 `application/handlers.py`: в course-сессии определять название из чанка и передавать `current_course`

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: промпт с/без текущего курса
- [x] 2.2 `tests/unit/test_handlers.py`: запрет в course-сессии, отсутствие в глобальной, «Источники» на месте

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate course-assistant-no-self-recommendation --strict`
- [x] 3.3 Живая проверка ответа внутри курса
