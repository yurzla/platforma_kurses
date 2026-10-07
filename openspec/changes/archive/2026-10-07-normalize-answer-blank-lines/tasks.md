## 1. Нормализация

- [x] 1.1 `domain/formatting.py`: `normalize_answer_spacing` (одна пустая строка между блоками,
  соседними пунктами и перед «Источники:»; fenced-блоки не трогаются)
- [x] 1.2 `application/handlers.py`: применить после санитайза в рекомендательной и RAG-ветках

## 2. Тесты

- [x] 2.1 `tests/unit/test_formatting.py`: пустые строки между пунктами/блоками, схлопывание,
  пустая строка перед «Источники:», неизменность код-блока
- [x] 2.2 `tests/unit/test_handlers.py`: сохранённый рекомендательный ответ содержит пустые строки

## 3. Проверка

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate normalize-answer-blank-lines --strict`
