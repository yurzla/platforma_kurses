## 1. Specification

- [x] 1.1 Описать семантику размера очереди индексации в дельте `ops-dashboard`.

## 2. Backend

- [x] 2.1 Добавить `queue_size` в `IndexQueueState` и вычислять его как `pending + lag` в
  `/api/v1/admin/index`.

## 3. Web

- [x] 3.1 Перепривязать карточку «в очереди на индексацию» к `queue_size`, добавить карточку
  «сообщений в стриме» (`length`).
- [x] 3.2 Уточнить заголовок `Length (всего)` и описание вкладки Streams.

## 4. Verification

- [x] 4.1 Обновить проверки статики дашборда и интеграционную проверку очереди.
- [x] 4.2 `make lint`, `make typecheck`, `make test`, `openspec validate index-queue-metrics --strict`.
