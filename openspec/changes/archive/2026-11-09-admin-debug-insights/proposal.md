# Proposal

## Why

Админ-панель показывает только списки job-ов, DLQ и Redis Streams. При разборе
проблем с ответами ассистента не видно, какие источники использовались, что
содержится в конкретном чанке, в каком состоянии RAG-индекс и доступны ли
зависимости. Это заставляет разработчика ходить в БД и логи вместо диагностики
из интерфейса.

## What Changes

- В «Технической диагностике» добавить подвкладки **Индекс** и **Состояние**.
- Сделать строки Jobs кликабельными и показывать детали job: вопрос, ответ,
  переписанный вопрос, ошибку, попытки, время и использованные источники.
- Добавить просмотр текста чанка и списка чанков с фильтрами по курсу, типу
  источника и поиском по тексту.
- Добавить сводку по RAG-индексу: количество чанков и эмбеддингов, чанки без
  эмбеддинга, разбивка по типам и курсам, модель/размерность и дата последнего
  эмбеддинга.
- Добавить сводку состояния: Postgres, Redis, Ollama и наличие модели
  эмбеддингов, последние метки завершённых/упавших/ожидающих job-ов и текущие
  настройки retrieval.
- Новые read-only эндпоинты: `GET /api/v1/admin/chunks`,
  `GET /api/v1/admin/chunks/{chunk_id}`, `GET /api/v1/admin/index`,
  `GET /api/v1/admin/health`.

Только чтение. Retry job, replay DLQ, удаление и отмена job, изменения очередей
и статусов не входят.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `ops-dashboard`: добавляются требования к read-only просмотру деталей job,
  чанков и эмбеддингов, сводке RAG-индекса и состоянию зависимостей.

## Impact

- `backend/src/courses_assistant/entrypoints/api/routers/admin.py` — новые
  read-only эндпоинты.
- `backend/src/courses_assistant/entrypoints/api/schemas.py` — схемы чанков,
  индекса и состояния.
- `backend/src/courses_assistant/adapters/embeddings/ollama.py` — проверка
  доступности Ollama и наличия модели.
- `web/src/courses_web/templates/dashboard.html`,
  `web/src/courses_web/static/dashboard.{js,css}` — новые подвкладки, модалки и
  таблицы.
- `tests/api/test_admin.py`, `tests/integration/`, `tests/web/test_web.py` —
  проверки доступа и отображения.
- `README.md` — описание вкладок и эндпоинтов.
