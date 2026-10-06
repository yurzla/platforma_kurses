## 1. Backend

- [x] 1.1 `config.py`: `catalog_prompt_limit: int = 50`
- [x] 1.2 `domain/prompts.py`: `build_course_catalog`, правило про каталог в `SYSTEM_PROMPT`, `build_answer_system_prompt(context, catalog)`, `build_answer_messages(..., catalog)`
- [x] 1.3 `application/rag.py`: параметр `catalog` у `generate_answer`
- [x] 1.4 `application/handlers.py`: в глобальной сессии получать каталог и передавать в промпт; отвечать по каталогу, когда чанков нет, а каталог есть

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: каталог в system-промпте, пометка «вы записаны»
- [x] 2.2 `tests/unit/test_handlers.py`: глобальный вопрос без чанков, но с каталогом → ответ; курсовая без чанков и глобальная без каталога → `NO_MATERIALS_ANSWER`

## 3. Документация

- [x] 3.1 `README.md`/`AGENTS.md`: ассистент рекомендует курсы из каталога в глобальных чатах

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate --all --strict`
- [x] 4.2 Пересборка `api`/`worker`/`scheduler`/`cron`, e2e: вопрос «какой курс посоветуешь, чтобы изучить Python?» → реальные названия курсов
