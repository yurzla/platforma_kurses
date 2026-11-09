# Proposal

## Why

CI-job `lint` падает на pre-existing ошибках `ruff` и `mypy` в коде
преподавателя, администратора и репозиториев. Из-за этого нельзя получить
зелёный CI и подтвердить, что восстановление фич из `Refac-architecture`
ничего не сломало.

## What Changes

- Исправить 71 замечание `ruff`: длинные строки, несколько statement через
  `;`, порядок импортов и лишние кавычки в аннотациях.
- Исправить 4 ошибки `mypy`: приведение результата `delete()` к
  `CursorResult` и конфликт имени `user` с типом `User` в админ-роутере.
- Поведение API, схемы и БД не меняются.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

Нет: изменение не меняет поведение, поэтому в `.openspec.yaml` указан
`skip_specs: true`.

## Impact

- `backend/src/courses_assistant/entrypoints/api/routers/{teacher,admin}.py`
- `backend/src/courses_assistant/entrypoints/api/{app.py,schemas.py}`
- `backend/src/courses_assistant/adapters/persistence/repositories.py`
- `backend/alembic/versions/0008_teacher_courses.py`
- `web/src/courses_web/routers/pages.py`
