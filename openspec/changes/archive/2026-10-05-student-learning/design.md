## Context

Курсы, шаги и прогресс уже есть в схеме (`courses`, `sections`, `lessons`, `steps`, `step_contents`, `user_step_progress`, `enrollments`), но нет портов/эндпоинтов для их выдачи студенту.

## Goals / Non-Goals

- Goals: сквозной сценарий обучения; серверная оценка; прогресс в БД.
- Non-Goals: запись аудио/видео ответов, ручная проверка преподавателем, регистрация студентов через UI.

## Decisions

- **Порты `UserRepository` и `CatalogRepository`** в `application/ports.py`; реализации `Sql*` и in-memory фейки. `UnitOfWork` получает `users` и `catalog`.
- **`CatalogRepository` отдаёт санитизированные `StepDetail`**: для choice — варианты без `is_correct`; ключ доступен серверу через `get_answer_key`.
- **Оценка в `domain/quiz.py`** (`build_answer_key`, `grade`, `grading_mode`) — чистая функция; обработчик `SubmitStepAnswer` применяет её и пишет результат.
- **Прогресс**: upsert `user_step_progress` (status/best_score/attempts) и пересчёт `enrollments.progress_percent`; авто-типы — `choice`/`number`/`string`, остальные — manual.
- **Web** рендерит страницы каталога; ответы отправляются из `web.js` через прокси.

## Risks / Trade-offs

- Проверка владельца шага: `get_step` фильтрует по `course_id`, чтобы нельзя было читать чужие шаги.
- Concurrency upsert прогресса выполняется select+update внутри транзакции (UQ `(user_id, step_id)` добавлен миграцией).
