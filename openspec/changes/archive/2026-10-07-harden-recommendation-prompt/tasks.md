## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 6 — рекомендовать ТОЛЬКО курсы из раздела «РЕКОМЕНДУЕМЫЕ КУРСЫ»; запрет курсов из истории/материалов/знаний; поведение на «ещё» при исчерпанном списке; при пустом/отсутствующем разделе не перечислять курсы

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: `test_system_prompt_forbids_extra_courses`

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate harden-recommendation-prompt --strict`
