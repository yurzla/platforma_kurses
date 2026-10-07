## 1. Контекст и промпт

- [x] 1.1 `domain/context.py`: метка `[Источник i]` → `[Материал i]`
- [x] 1.2 `domain/prompts.py`: правило 7 запрещает собственные метки «Источник»/«Источники»/«Sources»

## 2. Тесты

- [x] 2.1 `tests/unit/test_domain.py`: проверка новой метки контекста
- [x] 2.2 `tests/unit/test_domain.py`: проверка запрета метки в системном промпте

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate avoid-model-sources-label --strict`
- [x] 3.3 Живая проверка глобального ответа — одна секция «Источники:»
