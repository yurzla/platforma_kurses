## Why

Платформа хранит курсы, шаги и прогресс в БД, но студент не может войти и пройти материал: нет аутентификации студентов и каталога обучения. Нужен сквозной сценарий «вход → курсы → шаг → прогресс».

## What Changes

- Аутентификация студентов по email/паролю из таблицы `users` (scrypt-хэши), сессия в API.
- JSON-каталог: список курсов с прогрессом, курс (секции/уроки/шаги), шаг, отправка ответа.
- Ответы оцениваются на сервере; правильные ключи не отдаются клиенту; прогресс пишется в `user_step_progress` и пересчитывается в `enrollments.progress_percent`.
- Скрипт `scripts/create_user.py` для создания/обновления пользователей.

## Capabilities

### New Capabilities
- `student-auth`: вход/выход студента и определение текущего пользователя.
- `learning-catalog`: каталог курсов, шагов и отправка ответов с прогрессом.

### Modified Capabilities
<!-- нет -->

## Impact

- Домен: `domain/catalog.py`, `domain/security.py`, `domain/models.User`, `domain/quiz.py`.
- Порты/адаптеры: `UserRepository`, `CatalogRepository` (+ `Sql*`), `UnitOfWork`, фейки.
- Команда `SubmitStepAnswer`, обработчик в `handlers.py`.
- API: `routers/auth.py` (student), `routers/catalog.py`, `schemas.py`.
- Web: страницы `/courses`, `/courses/{id}`, `/courses/{id}/steps/{step_id}`.
- Тесты: `tests/api/test_student_auth.py`, `tests/api/test_catalog.py`, `tests/unit/test_quiz.py`.
