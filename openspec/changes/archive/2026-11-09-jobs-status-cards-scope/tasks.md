# Tasks

## 1. Web

- [x] 1.1 Перенести `#status-cards` внутрь `#diagnostic-jobs` — проверка: карточки видны только на Jobs
- [x] 1.2 Убедиться, что клики по карточкам и `loadOverview()` работают без изменений — проверка: фильтр Jobs применяется, Streams обновляются

## 2. Tests

- [x] 2.1 Проверить расположение `#status-cards` в web-тесте — проверка: `pytest tests/web/test_web.py`

## 3. Verification

- [x] 3.1 Прогнать `ruff`, `mypy`, `pytest` — проверка: все проверки зелёные
- [x] 3.2 Проверить `openspec validate jobs-status-cards-scope --strict` — проверка: без ошибок
- [x] 3.3 Пересобрать web и проверить на 8080 — проверка: карточки только на Jobs

## Workflow follow-up

- Архивировать изменение.
- Перезапустить web на 8080 без коммита портовых настроек.
