# Tasks

## 1. Fix

- [x] 1.1 Заменить `{{ course_id }}` на `{{ course.id }}` в `web/src/courses_web/templates/_step_form.html`
- [x] 1.2 Добавить регрессионную проверку в `tests/web/test_web.py`

## 2. OpenSpec

- [x] 2.1 Добавить delta-спеку `web-interface`; проверить `openspec validate fix-step-form-course-id --strict`
- [x] 2.2 Заархивировать изменение

## 3. Проверка

- [x] 3.1 Прогнать `uv run ruff check .`, `uv run mypy` и `uv run pytest`
- [x] 3.2 Пересобрать и перезапустить web-сервис локально
