# Tasks

## 1. OpenSpec

- [x] 1.1 Добавить delta-спеки `teacher-workspace`, `learning-catalog`, `web-interface`; проверить `openspec validate add-step-editing-and-video --strict`

## 2. Backend: видео и данные шага

- [x] 2.1 Добавить миграцию `0009_step_video_url`, `StepORM.video_url`, `StepDetail.video_url`, `StepRead.video_url`
- [x] 2.2 Реализовать `domain/video.py` с нормализацией ссылок и тестами
- [x] 2.3 Отдавать видео-ссылку в `get_step` и рендерить её на странице шага

## 3. Backend: управление шагами

- [x] 3.1 Расширить детали курса преподавателя данными шага для формы
- [x] 3.2 Реализовать `PATCH /api/v1/teacher/steps/{step_id}` и `DELETE /api/v1/teacher/steps/{step_id}`; поддержать `video_url` при создании
- [x] 3.3 Покрыть API-тестами обновление по типам, удаление, перенумерацию и права доступа

## 4. Web

- [x] 4.1 Вынести `_step_form.html`, перестроить раскладку полей и кнопок
- [x] 4.2 Добавить инлайн-редактирование и удаление шагов на странице курса
- [x] 4.3 Добавить подсказку по форматированию и рендер видео
- [x] 4.4 Обновить `teacher.js` и `web.css`; проверить web-тестами

## 5. Проверка

- [x] 5.1 Прогнать `uv run ruff check .` и `uv run mypy`
- [x] 5.2 Прогнать `uv run pytest` с `INTEGRATION_DATABASE_URL` и `INTEGRATION_REDIS_URL`
- [x] 5.3 Проверить `uv lock --check` и обе Docker-сборки
- [x] 5.4 Перезапустить локальный стек с миграцией

## Workflow follow-up

- Заархивировать change после зелёных проверок.
- Закоммитить и запушить в `feature/platform-development-merged`.
