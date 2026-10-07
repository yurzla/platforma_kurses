## Why

В сессии, привязанной к курсу, ассистент иногда предлагал пройти тот же курс, внутри которого студент уже находится (например, «На платформе есть курс … „Анализ данных в R“»). Это сбивает с толку: курс уже выбран.

## What Changes

- В системный промпт ответа для сессии, привязанной к курсу, добавляется указание: студент уже внутри этого курса, не предлагать пройти/записаться/выбрать его.
- Секция «Источники» не меняется и по-прежнему добавляется всегда при наличии материалов.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: в course-сессии промпт запрещает предлагать пройти текущий курс.

## Impact

- Backend: `domain/prompts.py` (`build_answer_system_prompt`, `build_answer_messages`), `application/rag.py` (`generate_answer`), `application/handlers.py` (`process_question` передаёт текущий курс).
- Tests: `tests/unit/test_domain.py`, `tests/unit/test_handlers.py`.
- Web, БД, миграции: без изменений.
