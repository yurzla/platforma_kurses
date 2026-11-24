## 1. Domain

- [x] 1.1 Заменить `ensure_course_link` на `build_sources_section` в `domain/prompts.py` (подпись «Источники», все курсы, дедуп); проверить unit-тестами
- [x] 1.2 Уточнить `SYSTEM_PROMPT`: отдельный список источников не добавлять; проверить тестом

## 2. Application и адаптеры

- [x] 2.1 В `process_question` собирать уникальные курсы-источники из чанков и добавлять секцию «Источники» при их наличии; проверить handler-тестами
- [x] 2.2 Удалить неиспользуемый `get_course_summary` из порта, SQL-репозитория и фейков; проверить mypy

## 3. Tests

- [x] 3.1 Обновить `tests/unit/test_domain.py`: тесты `build_sources_section`
- [x] 3.2 Обновить `tests/unit/test_handlers.py`: секция «Источники» для course/global, отсутствие секции без материалов
- [x] 3.3 Обновить `tests/api/test_api.py`: секция «Источники» в ответе

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit` — зелёные
- [x] 4.2 Пересобрать контейнеры и проверить ответ на «курсы по js»: секция «Источники» со ссылками
- [x] 4.3 `openspec validate course-sources-block --strict` и архивация
