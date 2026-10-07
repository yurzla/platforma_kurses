## Why

Прогоны показали, что модель не соблюдает форматирование: пункты списка не разделяются пустой
строкой, хотя промпт это требует. Нужна детерминированная гарантия форматирования.

## What Changes

- Новый чистый модуль `domain/formatting.py` с функцией `normalize_answer_spacing`, приводящей
  ответ к ровно одной пустой строке между блоками, между соседними пунктами списка и перед
  «Источники:»; содержимое fenced-блоков не изменяется.
- `application/handlers.py` применяет нормализацию после санитайза в рекомендательной и RAG-ветках.
- Промпт (правило 9) не меняется; нормализация — дополнительная гарантия.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-chat`: требование `Markdown-formatted answers` теперь гарантирует детерминированную
  нормализацию пустых строк перед сохранением ответа.

## Impact

- Backend: `domain/formatting.py` (новый), `application/handlers.py`.
- Tests: `tests/unit/test_formatting.py` (новый), `tests/unit/test_handlers.py`.
