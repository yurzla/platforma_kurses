## 1. Промпт

- [x] 1.1 `domain/prompts.py`: правило 7 — блок «Источники» только из курсов переданных данных, посторонние курсы/заголовки отбрасывать; исключение — нет ни одного курса-источника
- [x] 1.2 `domain/prompts.py`: правило 9 — ровно одна пустая строка между блоками и между пунктами списка, пустая строка перед «Источники:»

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: обновить `test_system_prompt_requests_sources_block` и `test_system_prompt_requests_blank_line_separation`

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate discard-unknown-sources-and-blank-lines --strict`
