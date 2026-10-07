## 1. Domain

- [x] 1.1 `build_sources_section(courses, answer, *, always_ids)` в `domain/prompts.py`: фильтр по упоминанию названия/ссылки, форс `always_ids`, пустая строка при отсутствии; проверить unit-тестами

## 2. Application

- [x] 2.1 В `process_question` передавать `always_ids={session.course_id}` для сессии по курсу и добавлять секцию только если она непустая; проверить handler-тестами

## 3. Tests

- [x] 3.1 `tests/unit/test_domain.py`: упоминание по названию/ссылке, пропуск неупомянутого, `always_ids`, пустой результат
- [x] 3.2 `tests/unit/test_handlers.py`: глобальный ответ с/без упоминания источника; курс-сессия включает курс всегда

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit` — зелёные
- [x] 4.2 Пересобрать контейнеры и проверить запрос: в «Источниках» нет неупомянутых курсов
- [x] 4.3 `openspec validate sources-only-mentioned-courses --strict` и архивация
