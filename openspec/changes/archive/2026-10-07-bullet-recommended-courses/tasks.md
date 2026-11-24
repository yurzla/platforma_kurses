## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 6 — маркированный список курсов, запрет перечисления через запятую

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_forbids_extra_courses` — новые ассерты

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate bullet-recommended-courses --strict`
