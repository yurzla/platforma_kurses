## Why

Кнопка ассистента закреплена в левом нижнем углу и перекрывает сайдбар страницы курса; справа внизу она не мешает навигации и ожидаемее для пользователя.

## What Changes

- Кнопка ассистента (`#assistant-toggle`) переносится из левого нижнего угла в правый нижний.
- Поведение чат-панели (открывается справа поверх страницы) не меняется.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-interface`: требование «Floating RAG assistant widget» — кнопка закреплена в правом нижнем углу.

## Impact

- Web-статика: `web/src/courses_web/static/web.css` (`.assistant-fab`).
- Тесты: `tests/web/test_web.py` (проверка позиции кнопки).
- API/backend не меняются.
