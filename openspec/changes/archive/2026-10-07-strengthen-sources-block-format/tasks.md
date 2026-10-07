## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 7 — обязательный блок `Источники:` со списком `- [«Название курса»](/courses/ID)`, запрет метки-номера вместо названия

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_requests_sources_block` проверяет формат и запрет «Источник 1»

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate strengthen-sources-block-format --strict`
