## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 7 — блок `Источники:` в одну строку, ссылки через запятую

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_requests_sources_block` проверяет формат через запятую

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate comma-separated-sources-list --strict`
