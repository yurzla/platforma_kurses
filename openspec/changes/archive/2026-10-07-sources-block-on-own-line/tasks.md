## 1. Нормализация

- [x] 1.1 `domain/formatting.py`: `_split_inline_sources_label` — вынос метки «Источники:» на свою строку

## 2. Тесты

- [x] 2.1 `tests/unit/test_formatting.py`: разбиение склеенной метки, код-блок не трогается
- [x] 2.2 `tests/unit/test_handlers.py`: сохранённый ответ содержит «Источники:» с отдельной строки

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate sources-block-on-own-line --strict`
