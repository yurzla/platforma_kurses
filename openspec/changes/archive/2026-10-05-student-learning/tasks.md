## 1. Домен и порты

- [x] 1.1 `domain/security.py` (scrypt hash/verify), `domain/models.User`.
- [x] 1.2 `domain/catalog.py` (CourseSummary/Detail, Section/Lesson/StepSummary, StepDetail, StepResult).
- [x] 1.3 `domain/quiz.py` (answer key, grading).
- [x] 1.4 Порты `UserRepository`, `CatalogRepository`; `UnitOfWork.users`/`catalog`.
- [x] 1.5 Адаптеры `SqlUserRepository`, `SqlCatalogRepository`; фейки.

## 2. API

- [x] 2.1 `POST /api/v1/auth/student/login|logout`, `GET /api/v1/auth/me` (student).
- [x] 2.2 `GET /api/v1/courses`, `/courses/{id}`, `/courses/{id}/steps/{step_id}`.
- [x] 2.3 `POST /api/v1/courses/{id}/steps/{step_id}/answer`.
- [x] 2.4 Зависимость `require_student`; схемы каталога/ответа.

## 3. Web

- [x] 3.1 Страницы `/courses`, `/courses/{id}`, `/courses/{id}/steps/{step_id}`.
- [x] 3.2 `web.js`: отправка ответа, отображение результата.
- [x] 3.3 Ссылка и отображение прогресса.

## 4. Скрипты и тесты

- [x] 4.1 `scripts/create_user.py`.
- [x] 4.2 `tests/unit/test_quiz.py`, `tests/api/test_student_auth.py`, `tests/api/test_catalog.py`.
- [x] 4.3 `ruff → mypy → pytest`.
