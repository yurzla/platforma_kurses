# Proposal

## Why

CI-job `test` поднимает пустую PostgreSQL и применяет миграции с нуля. В этом
режиме интеграционный тест рекомендателя падает на удалении курсов: тест
удаляет `courses` раньше связанных `content_chunks`/`chunk_embeddings`, а
`0001_baseline` создаёт FK без `ON DELETE CASCADE` (в демо-дампе каскад есть,
поэтому локально ошибка не воспроизводится).

## What Changes

- Исправить порядок очистки в
  `tests/integration/test_recommender.py`: сначала embeddings, затем chunks,
  затем courses.
- Добавить недостающий импорт `select`.
- Продовая схема, ORM и миграции не меняются.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет: изменение затрагивает только тестовую очистку, поэтому в
`.openspec.yaml` указан `skip_specs: true`.

## Impact

- `tests/integration/test_recommender.py`
- Проверка: чистая БД + `alembic upgrade head` + полный `pytest`.
