## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 9 — пустая строка между блоками ответа и между пунктами списков

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_requests_blank_line_separation`

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate blank-line-separated-blocks --strict`
