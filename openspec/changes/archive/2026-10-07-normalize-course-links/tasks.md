## 1. Бэкенд

- [x] 1.1 `domain/recommendations.py`: `_LINK_RE` допускает пробелы; `_strip_unknown_links` возвращает канонический вид ссылки
- [x] 1.2 `domain/prompts.py`: правило 8 — ссылка без пробелов

## 2. Web

- [x] 2.1 `static/assistant-format.js`: паттерн допускает пробелы, target обрезается `.trim()`

## 3. Тесты

- [x] 3.1 `tests/unit/test_recommendations.py`: нормализация разрешённой ссылки с пробелами
- [x] 3.2 `tests/unit/test_recommendations.py`: неизвестная ссылка с пробелами разворачивается в текст

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test`
- [x] 4.2 `openspec validate normalize-course-links --strict`
- [x] 4.3 Живая проверка: ссылка на курс рендерится кликабельной
