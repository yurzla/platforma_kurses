# Tasks

## 1. Исправление теста

- [x] 1.1 Исправить `finally` в `tests/integration/test_recommender.py`: собрать `chunk_ids`, удалить `ChunkEmbeddingORM`, затем `ContentChunkORM`, затем `CourseORM`; добавить импорт `select`
- [x] 1.2 Проверить файл через `uv run ruff check tests/integration/test_recommender.py`

## 2. Проверка как в CI

- [x] 2.1 Создать пустую БД, применить `alembic upgrade head` и прогнать полный `uv run pytest` с CI-переменными
- [x] 2.2 Прогнать `uv run ruff check .`, `uv run mypy` и `uv lock --check`
- [x] 2.3 Проверить Docker-сборки backend и web

## Workflow follow-up

- Закоммитить и запушить исправление в `feature/platform-development-merged`.
- Заархивировать change после зелёных проверок.
