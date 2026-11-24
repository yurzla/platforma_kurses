## 1. Specification

- [x] 1.1 Описать дельты `ops-dashboard` (DLQ по всем стримам, расширенные метрики, очередь
  индексации, живость воркеров, изменения страницы).

## 2. Backend

- [x] 2.1 Расширить контракт `MessageBroker.stream_stats` и реализацию `RedisStreamsBroker`
  (`exists`, `last_generated_id`, `last_delivered_id`, `entries_read`, `last_message_at`,
  `consumer_details`), устойчиво к отсутствующим стримам и группам.
- [x] 2.2 Обновить фейк брокера в `tests/fakes.py`.
- [x] 2.3 `/api/v1/admin/dlq`: агрегировать `rag.dead`, `rag.index.dead`, `rag.cron.dead`,
  добавить `dead_stream` и фильтр `?stream=`, стабильная сортировка по времени.
- [x] 2.4 `/api/v1/admin/streams` и `/overview`: новые поля `StreamStat` и признак `kind`.
- [x] 2.5 `/api/v1/admin/index`: блок `queue` (length/pending/lag/consumers/exists, dead_letters).
- [x] 2.6 `/api/v1/admin/health`: блок `workers` по группам chat/indexer/cron.
- [x] 2.7 Обновить pydantic-схемы в `entrypoints/api/schemas.py`.

## 3. Web

- [x] 3.1 DLQ: фильтр по dead-stream и колонка «Очередь».
- [x] 3.2 Streams: колонки «Тип», «Последнее сообщение», «Консьюмеры», подсветка `pending/lag`.
- [x] 3.3 Index: карточки очереди индексации и ошибок.
- [x] 3.4 Health: блок «Воркеры».
- [x] 3.5 Явная загрузка метрик стримов на вкладке Streams.

## 4. Verification

- [x] 4.1 API-тесты: DLQ из index-стрима, фильтр по `dead_stream`, новые поля метрик, очередь в
  `/index`, воркеры в `/health`, доступ только для admin.
- [x] 4.2 Web-smoke дашборда (наличие новых элементов и запросов).
- [x] 4.3 `make lint`, `make typecheck`, `make test`, `openspec validate ops-queue-observability --strict`.
