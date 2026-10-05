## 1. Конфигурация и порты

- [x] 1.1 Добавить настройки ретенции и cron в `config.py` (`stream_cron`, `cron_dlq`, `cron_group`, `cron_consumer_name`, `cron_interval_seconds`, `job_retention_days`, `redis_stream_maxlen`, `redis_stream_events_maxlen`, `admin_token`) и обновить `.env.example` — проверка: `pytest tests/unit` зелёный, `Settings` читает значения
- [x] 1.2 Расширить порты: `MessageBroker.publish(..., maxlen)`, `move_to_dead(..., maxlen)`, `read_dead`, `stream_stats`; `JobRepository.list/count/status_counts/purge_terminal` — проверка: `mypy src` без ошибок

## 2. Ретенция

- [x] 2.1 Реализовать обрезку стримов (`XADD ... MAXLEN ~`) в `redis_streams.py` — проверка: `tests/integration/test_broker.py` (maxlen) проходит
- [x] 2.2 Реализовать `purge_terminal` в `repositories.py` — проверка: `tests/integration/test_jobs_repository.py` проходит
- [x] 2.3 Добавить миграцию `alembic/versions/0004_jobs_updated_at_index.py` (`CREATE INDEX IF NOT EXISTS`) — проверка: `alembic upgrade head` применяется на чистой и заполненной БД

## 3. Cron-очередь

- [x] 3.1 Вынести общий consumer-loop в `application/consumer.py` (`consume_loop`) и переиспользовать в `worker/main.py` — проверка: `pytest tests/unit/test_handlers.py` и smoke ask-flow зелёные
- [x] 3.2 Реализовать команду `RunCronTask` и обработчик `run_cron_task` — проверка: `tests/unit/test_handlers.py` покрывает успех, ошибку и неизвестную задачу
- [x] 3.3 Добавить entrypoints `scheduler` (публикует задачу по таймеру) и `cron` (консьюмер `rag.cron` с DLQ) — проверка: end-to-end прогон cron удаляет старый job (`deleted=1`)
- [x] 3.4 Зарегистрировать скрипты в `pyproject.toml` и сервисы `scheduler`/`cron` в `docker-compose.yml` — проверка: `docker compose config -q` и 7 сервисов healthy

## 4. Дашборд и админ-API

- [x] 4.1 Добавить запросы `list_jobs`, `job_status_counts`, `dlq_entries`, `stream_overview` — проверка: `pytest tests/api/test_admin.py` проходит
- [x] 4.2 Описать схемы `JobListItem`, `JobListResponse`, `DlqEntry`, `StreamStat`, `OverviewResponse` — проверка: ответы эндпоинтов соответствуют схемам
- [x] 4.3 Реализовать `routers/admin.py` (`/api/v1/admin/*`) и `routers/dashboard.py` (`GET /dashboard`) — проверка: `/dashboard` отдаёт 200 HTML, admin-endpoints возвращают counts/jobs/dlq/streams
- [x] 4.4 Реализовать `require_admin`/`admin_token_ok` и связать с `ADMIN_TOKEN` — проверка: без токена при заданном `ADMIN_TOKEN` — 401, с токеном — 200, без токена в конфиге — открыто
- [x] 4.5 Добавить шаблоны `templates/{base,dashboard}.html` и статику `static/{dashboard.css,dashboard.js}`; добавить `jinja2` и подключить статику в `app.py` — проверка: `/static/*` отдают 200

## 5. Верификация и документация

- [x] 5.1 Прогнать `ruff check .`, `mypy src`, `pytest` — проверка: все зелёные (mypy: 53 файла)
- [x] 5.2 Compose smoke: поднять стек, проверить ask-flow, cron end-to-end, дашборд и админ-API — проверка: 7 сервисов healthy, `deleted=1`, `/dashboard` и `/api/v1/admin/*` отвечают
- [x] 5.3 Обновить `README.md` и `Makefile` (сервисы, переменные, команды) — проверка: инструкция воспроизводит запуск на чистом checkout
- [x] 5.4 Задокументировать изменение в OpenSpec и синхронизировать спеки — проверка: `openspec validate --strict` зелёный, архив содержит новый change
