# Tasks

## 1. OpenSpec

- [x] 1.1 Добавить delta-спеки `learning-catalog`, `web-interface` и новую capability `teacher-workspace`; проверить `openspec validate add-course-search-and-teacher-pagination --strict`

## 2. Backend: поиск в каталоге

- [x] 2.1 Добавить `search` в `CatalogRepository.list_courses`/`count_courses`, SQL-репозиторий и `GET /api/v1/courses`; проверить API-тесты поиска
- [x] 2.2 Реализовать поиск в `InMemoryCatalogRepository`; проверить `tests/api/test_catalog.py`

## 3. Backend: список преподавателя

- [x] 3.1 Добавить `TeacherCourseSummary`, методы `list_authored_courses`/`count_authored_courses`, SQL-реализацию и ответ `TeacherCourseListResponse`
- [x] 3.2 Перевести `GET /api/v1/teacher/courses` на UoW-репозиторий с `search`, `limit`, `offset`; проверить новые API-тесты

## 4. Web

- [x] 4.1 Добавить поиск на `/courses` и `/my-courses`, сохранить `search` в пагинации и клампинге; проверить web-тесты
- [x] 4.2 Добавить пагинацию и поиск на `/teacher`, обновить форму создания и пустые состояния; проверить web-тесты

## 5. Проверка

- [x] 5.1 Прогнать `uv run ruff check .` и `uv run mypy`
- [x] 5.2 Прогнать `uv run pytest` с `INTEGRATION_DATABASE_URL` и `INTEGRATION_REDIS_URL`
- [x] 5.3 Проверить `uv lock --check` и обе Docker-сборки

## Workflow follow-up

- Закоммитить и запушить изменения в `feature/platform-development-merged`.
- Заархивировать change после зелёных проверок.
