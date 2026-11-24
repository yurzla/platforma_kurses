## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 7 — блок «Источники:» обязателен, исключение только для ответа «Больше подходящих курсов в списке нет.»

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_requests_sources_block` проверяет исключение

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate sources-block-except-no-more --strict`
