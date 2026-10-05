## Why

Тесты курсов нельзя проверить автоматически: ключи ответов есть только в Stepik `/api/step-sources`, которых нет в дампе. Кроме того, RAG-ассистент доступен только через API — нужен интерфейс в web для студента.

## What Changes

- Импорт ключей ответов из Stepik в таблицу `step_sources` (`scripts/import_step_sources.py`) и разбор/оценка в `domain/quiz.py`.
- Новый тип `choice`/`number`/`string` — авто-проверка; остальные — manual; при отсутствии ключа шаг помечается manual.
- Прокси создания чат-сессии выводит пользователя из сессии студента (если аутентифицирован).
- В web-странице шага — панель «Ассистент»: создание сессии, вопрос (202), polling job, показ ответа.

## Capabilities

### New Capabilities
- `quiz-grading`: импорт ключей Stepik и серверная автопроверка ответов.

### Modified Capabilities
- `rag-chat`: создание чат-сессии может выводить пользователя из аутентифицированной сессии студента; веб-интерфейс ассистента.

## Impact

- ORM `StepSourceORM`, миграция `0005_step_sources` (+ unique index прогресса), baseline исключает `step_sources`.
- `domain/quiz.py`, `CatalogRepository.get_answer_key`, обработчик `SubmitStepAnswer`.
- `scripts/import_step_sources.py`, `pyproject.toml`.
- `routers/chat.py` (session user), `web/templates/step.html`, `web/static/web.js`.
- Тесты `tests/unit/test_quiz.py`, каталог-тесты.
