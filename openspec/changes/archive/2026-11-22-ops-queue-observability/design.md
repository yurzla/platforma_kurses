# Design

## Контекст

Диагностика сосредоточена в `entrypoints/api/routers/admin.py`, метрики очередей отдаёт порт
`MessageBroker` (`application/ports.py`), реализация — `adapters/broker/redis_streams.py`.
Веб-часть — `web/src/courses_web/templates/dashboard.html` и `static/dashboard.js`, данные
тянутся через встроенный прокси `/api/*`.

Сейчас:

- `/api/v1/admin/dlq` читает `rag.dead` и `rag.cron.dead`, но не `rag.index.dead`;
- `stream_stats` возвращает только `length/pending/lag/consumers`;
- `/api/v1/admin/index` считает данные БД, но не состояние очереди индексации;
- `/api/v1/admin/health` проверяет Postgres/Redis/Ollama, но не живость воркеров.

## Решения

### 1. Расширение порта `MessageBroker.stream_stats`

Не добавляем новый метод, а расширяем словарь существующего — так меньше изменений в фейках и
вызывающем коде. Новые ключи:

- `exists: bool`
- `kind: "processing" | "dead"` (вычисляется на уровне API из настроек, брокер возвращает только
  сырые данные; проще проставлять в роутере)
- `last_generated_id: str | None`
- `last_delivered_id: str | None`
- `entries_read: int | None`
- `last_message_at: datetime | None` — из миллисекундной части ID (`<ms>-<seq>`)
- `consumer_details: list[dict]` — `{name, pending, idle}` из `XINFO CONSUMERS`

В `RedisStreamsBroker` используем:

- `EXISTS` для `exists`;
- `XINFO STREAM` для `last-generated-id` и длины;
- `XINFO GROUPS` для `pending/lag/consumers/last-delivered-id/entries-read`;
- `XINFO CONSUMERS` для детализации.

Любая `ResponseError` (нет стрима/группы) трактуется как «пусто», без исключения. `socket_timeout`
не задаём — правило проекта из-за блокирующего `XREADGROUP`; метрики неблокирующие.

### 2. DLQ по всем dead-letter стримам

`dlq()` собирает записи из `settings.stream_dead`, `settings.index_dlq`, `settings.cron_dlq`.
В каждую запись добавляется `dead_stream` (сам DLQ-стрим) рядом с уже существующим
`source_stream` (исходная очередь). Опциональный query-параметр `stream` фильтрует по
`dead_stream`.

Сортировка: по времени сообщения (ms из ID) по убыванию внутри объединённого списка, затем
ограничение `limit`. Так как ID уникальны только внутри стрима, сортируем по распарсенному
времени, а при равенстве сохраняем исходный порядок (стабильная сортировка).

### 3. Очередь индексации в `/index`

Дополнительный блок `queue`:

- `length`, `pending`, `lag`, `consumers`, `exists` — из `stream_stats(stream_index, index_group)`;
- `dead_letters` — `xlen(index_dlq)` через `stream_stats(index_dlq, index_group).length`.

Ошибки Redis не ломают сводку: при недоступности брокера блок отдаётся с нулями и
`available: false` (используем `container.broker.ping()`).

### 4. Живость воркеров в `/health`

Блок `workers` — список `{name, group, stream, consumers, available}` для групп:

- `chat` — `stream_requests` / `consumer_group`;
- `indexer` — `stream_index` / `index_group`;
- `cron` — `stream_cron` / `cron_group`.

`available = consumers > 0`. Данные берём из `stream_stats`, без проверки процессов.

### 5. Веб-дашборд

- DLQ: добавляем `<select id="dlq-stream">`, колонку «Очередь» (`dead_stream`) и подгрузку с
  `?stream=`.
- Streams: колонки «Тип», «Последнее сообщение», «Консьюмеры» (список `name (pending, idle)`);
  строка получает CSS-класс `warn`, если `pending > 0` или `lag > 0`. Явный `loadStreams()` при
  открытии вкладки; `loadOverview()` оставляем для карточек Jobs, чтобы не дублировать запросы.
- Index: карточки «В очереди», «Отставание», «Ошибок индексации» из блока `queue`.
- Health: таблица «Воркеры» из блока `workers`.

## Риски и границы

- `XINFO` может быть дорогим на очень длинных стримах, но дашборд опрашивается раз в 5 секунд и
  только на открытой вкладке; стримы ограничены `maxlen`.
- Совместимость: новые поля только добавляются, существующие клиенты не ломаются.
- Ретраев/переотправки DLQ не добавляем — изменение только про наблюдаемость.
