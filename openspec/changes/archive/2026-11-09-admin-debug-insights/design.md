# Design

## API

Все маршруты — под существующим `APIRouter(prefix="/api/v1/admin", dependencies=[Depends(require_admin)])`,
поэтому права проверяются до обращения к БД.

### `GET /api/v1/admin/chunks`

Query: `course_id: int | None`, `source_type: str | None`, `search: str | None`
(max 200), `limit` (1..200, по умолчанию 50), `offset` (>= 0).

Ответ `ChunkListResponse`:
- `items: list[ChunkListItem]`
- `total`, `limit`, `offset`

`ChunkListItem`: `id`, `course_id`, `course_title`, `lesson_id`, `lesson_title`,
`step_id`, `chunk_index`, `source_type`, `preview` (первые 240 символов),
`has_embedding`, `model_name`, `created_at`.

Запрос: `content_chunks` LEFT JOIN `courses`, `lessons`, `chunk_embeddings`.
Поиск — `chunk_text ILIKE %search%`, фильтр `source_type` — точное совпадение,
`course_id` — точное. Сортировка `ContentChunkORM.id`. `total` считается тем же
набором условий.

### `GET /api/v1/admin/chunks/{chunk_id}`

Ответ `ChunkDetail`: поля списка плюс `chunk_text` (полный) и
`embedding_dimension` (длина вектора; `None`, если эмбеддинга нет),
`embedding_created_at`. Не найдено → 404.

### `GET /api/v1/admin/index`

Ответ `IndexSummary`:
- `total_chunks`, `total_embeddings`, `chunks_without_embedding`;
- `by_source_type: dict[str, int]`;
- `model_name`, `dimension` — из настроек;
- `last_embedding_at: datetime | None`;
- `courses: list[IndexCourseSummary]`, где `IndexCourseSummary`: `id`, `title`,
  `chunks`, `description_chunks`, `step_chunks`, `embeddings`,
  `without_embedding`.

Курсы без чанков не попадают в список. Пустая БД возвращает нули и `[]`.

### `GET /api/v1/admin/health`

Ответ `AdminHealth`:
- `status`: `"ok"` | `"degraded"`;
- `dependencies: dict[str, str]` — `postgres`, `redis`, `ollama`;
- `ollama_model: str`, `ollama_model_available: bool`;
- `jobs: JobTimeline` — `last_done_at`, `last_failed_at`, `oldest_queued_at`;
- `settings: RetrievalSettings` — `embedding_model`, `embedding_dimension`,
  `retrieval_top_k`.

Postgres проверяется через `container.engine.connect()` + `SELECT 1`; Redis —
`container.broker.ping()`; Ollama — GET `/api/tags` (URL выводится из
`settings.ollama_url` заменой `/api/embed` на `/api/tags`) с таймаутом 3 с и
проверкой имени модели (сравнение до `:`). GigaChat не пингуется. Ошибки
зависимостей не роняют запрос: они попадают в `dependencies`. `status` равен
`"ok"` только если все три зависимости `"ok"`.

## Backend

- Схемы добавляются в `entrypoints/api/schemas.py`.
- Запросы к чанкам/индексу/таймлайну job-ов — прямо в `routers/admin.py` через
  `container.session_factory()` (как уже сделано для users/courses).
- Проверка Ollama — функция `check_ollama_model(base_url, model)` в
  `adapters/embeddings/ollama.py`, чтобы HTTP-детали не жили в роутере.
- Порт `Embedder` не меняется.

## Web

- Верхние вкладки не меняются. В «Технической диагностике» добавляются
  подвкладки `jobs`, `dlq`, `streams`, `index`, `health` (кнопка «Состояние»).
- Jobs: строки получают `data-job-id` и класс `clickable`; клик открывает
  модалку `#job-modal`, загружая `GET /admin/jobs/{id}`.
- В модалке источников `chunk_id` — кнопка, открывающая вложенную модалку
  `#chunk-modal` с `GET /admin/chunks/{id}`.
- Подвкладка «Индекс»: карточки totals, таблица по типам, таблица по курсам,
  фильтры и таблица чанков с пагинацией; клик по чанку открывает ту же модалку.
- Подвкладка «Состояние»: карточки зависимостей, метки job-ов и настройки.
- `refresh()` загружает данные только активной подвкладки; автообновление
  остаётся 5 с.
- `escapeHtml` используется для всех полей из API.

## Data safety

- Все новые маршруты — `GET`.
- Никаких `UPDATE`/`DELETE`/публикаций в очередях.
- Текст job-ов и чанков может содержать чувствительные данные, поэтому доступ
  только по роли `admin`.

## Testing

- Unit/API: отказ анониму (401) и не-админу (403) для всех четырёх маршрутов.
- Unit: `check_ollama_model` через `respx` — модель есть/нет/ошибка соединения.
- Интеграционные: сид курса, чанков и эмбеддингов, затем вызовы обработчиков
  `chunks`, `chunk_detail`, `index_summary`, `admin_health` с реальной сессией;
  проверка фильтров, `404`, `has_embedding` и `chunks_without_embedding`.
- Web: страница `/dashboard` содержит «Индекс» и «Состояние» и не содержит
  кнопок retry/replay.
