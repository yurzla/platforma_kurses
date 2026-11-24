## 1. Backend domain

- [x] 1.1 Расширить `RetrievedChunk` полями `course_id: int | None = None`, `course_title: str | None = None`; проверить, что старые тезы конструируют чанк без новых полей
- [x] 1.2 Ужесточить `SYSTEM_PROMPT` (только материалы курса + каталог портала, запрет внешних знаний, обязательная Markdown-ссылка на курс, рекомендации только из каталога) и добавить правильность рендера; проверить тестом `test_system_prompt_*`
- [x] 1.3 В `build_course_catalog` выводить `[«Title»](/courses/{id})`; проверить в `tests/unit/test_domain.py::test_build_course_catalog_marks_enrolled`
- [x] 1.4 Добавить чистую функцию `ensure_course_link(answer, links)` с дедупом по `/courses/{id}`; проверить тестами (дописывание и дедуп)
- [x] 1.5 В `build_context` добавлять строку `Курс: «Title» (/courses/ID)` при наличии данных курса; проверить тестом

## 2. Backend application

- [x] 2.1 Добавить `CatalogRepository.get_course_summary(course_id) -> CourseSummary | None` в порт; проверить mypy
- [x] 2.2 В `process_question` собирать релевантные `course_links` (курс сессии + уникальные курсы чанков) и вызывать `ensure_course_link` перед сохранением ответа; проверить unit-тестами
- [x] 2.3 Расширить `_chunk_to_source` полями `course_id`, `course_title`, `course_url`; проверить в тестах источников
- [x] 2.4 Гарантировать ссылку и для ответа «нет материалов» в сессии по курсу; проверить тестом

## 3. Backend adapters

- [x] 3.1 Реализовать `SqlCatalogRepository.get_course_summary` (лёгкий select без структуры); проверить mypy/pytest
- [x] 3.2 В `SqlCourseChunkRepository.search` join `CourseORM`, выбирать `course_id`/`title`, заполнять чанк; проверить интеграционным тестом при наличии БД

## 4. Web

- [x] 4.1 Расширить `renderInline` в `assistant-format.js`: рендер `[text](/path)` только для относительных путей, безопасная сборка DOM; проверить вручную в браузере
- [x] 4.2 Добавить стиль `.chat-link` в `web.css`; проверить визуально

## 5. Tests and fakes

- [x] 5.1 Обновить `tests/fakes.py`: `get_course_summary`, чанки с курсом; проверить, что фейки соответствуют портам
- [x] 5.2 Добавить/поправить unit-тесты `tests/unit/test_domain.py` и `tests/unit/test_handlers.py` (ссылка в каталоге, контекст, гарантия, источники)
- [x] 5.3 Поправить `tests/api/test_api.py` и `tests/web/test_web.py` при изменении формы sources; проверить прохождение

## 6. Verification

- [x] 6.1 Прогнать `make lint`, `make typecheck`, `make test-unit` — всё зелёное
- [x] 6.2 Вручную: ответ ассистента содержит кликабельную ссылку на курс
