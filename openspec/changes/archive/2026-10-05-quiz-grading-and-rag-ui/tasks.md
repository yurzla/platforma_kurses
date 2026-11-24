## 1. Ключи и миграция

- [x] 1.1 `StepSourceORM`; миграция `0005_step_sources` (таблица + unique index прогресса).
- [x] 1.2 Baseline исключает `step_sources`.
- [x] 1.3 `scripts/import_step_sources.py` + скрипт в `pyproject.toml`.

## 2. Оценка

- [x] 2.1 `domain/quiz.py`: `build_answer_key`, `grade`, `grading_mode`, `correct_answer_for_display`.
- [x] 2.2 `CatalogRepository.get_answer_key`; `SubmitStepAnswer` в `handlers.py`.
- [x] 2.3 Санитизация `StepDetail.options`.

## 3. RAG в web

- [x] 3.1 `chat` session: вывод пользователя из сессии студента.
- [x] 3.2 Панель «Ассистент» в `step.html` + логика в `web.js` (session → ask → poll).
- [x] 3.3 Проброс cookie через прокси для чата.

## 4. Тесты

- [x] 4.1 `tests/unit/test_quiz.py`; проверки каталога (grading/auto/manual).
- [x] 4.2 `ruff → mypy → pytest`.
