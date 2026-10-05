## Why

Служебные данные растут неограниченно: Redis-стримы (`rag.requests`, `rag.events`, `rag.dead`) никогда не обрезаются, а таблица `jobs` хранит завершённые задачи вечно. Оператору негде посмотреть статусы задач, DLQ и метрики очередей. Нужны ретенция, обзор и периодический maintenance, не смешанный с обработкой вопросов.

## What Changes

- **Ретенция Redis**: публикация в стримы с approximate `MAXLEN` (лимиты для requests/dead/cron и отдельный — для events).
- **Ретенция Postgres**: периодическое удаление завершённых (`done`/`failed`) job-ов старше N дней; индекс по `jobs.updated_at`.
- **Отдельная cron-очередь**: стрим `rag.cron` + собственный DLQ; сервис-планировщик публикует задачи по таймеру, сервис-cron-консьюмер их выполняет.
- **Дашборд (read-only)**: страница `/dashboard` (Jobs / DLQ / Streams) и админ-API `/api/v1/admin/*`; опциональный `ADMIN_TOKEN`.
- **Compose**: новые сервисы `scheduler` и `cron`.

Не является breaking: существующие HTTP-контракты не меняются, добавляются новые.

## Capabilities

### New Capabilities
- `job-retention`: ограничение роста служебных данных — обрезка Redis-стримов и удаление старых терминальных job-ов.
- `cron-queue`: отдельная очередь периодических задач с планировщиком и надёжным консьюмером.
- `ops-dashboard`: read-only обзор статусов job, DLQ и метрик стримов с опциональной авторизацией.

### Modified Capabilities
- `platform-health`: требование «Containerized runtime» расширяется — единый `docker compose up` поднимает также `scheduler` и `cron`.

## Impact

- Конфиг: `stream_cron`, `cron_group`, `cron_interval_seconds`, `job_retention_days`, `redis_stream_maxlen`, `redis_stream_events_maxlen`, `admin_token`.
- Порты: `MessageBroker.publish(..., maxlen)`, `move_to_dead(..., maxlen)`, `read_dead`, `stream_stats`; `JobRepository.list/count/status_counts/purge_terminal`.
- Новые entrypoints `scheduler` и `cron`; роутеры `admin`, `dashboard`; шаблоны/статика; зависимость `jinja2`.
- Alembic `0004_jobs_updated_at_index`; compose-сервисы `scheduler`, `cron`; README, `.env.example`, Makefile.
