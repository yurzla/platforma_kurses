## 1. Domain

- [x] 1.1 Создать `domain/recommendations.py` с `sanitize_course_recommendations(answer, allowed_courses)` и проверить unit-тестами
- [x] 1.2 Уточнить `SYSTEM_PROMPT` (`domain/prompts.py`): названия курсов внутри материалов урока не являются курсами платформы и не рекомендуются; проверить тестом

## 2. Application

- [x] 2.1 Собрать разрешённое множество курсов в `process_question` (каталог ∪ курсы чанков ∪ курс сессии) и вызвать фильтр до `ensure_course_link`; проверить handler-тестом

## 3. Tests

- [x] 3.1 `tests/unit/test_recommendations.py`: удаление фейкового пункта, сохранение реального, разворачивание невалидной ссылки, сохранение валидной ссылки, удаление вложенных подпунктов
- [x] 3.2 `tests/unit/test_handlers.py`: воспроизвести кейс session 14 (ответ LLM с вымышленным курсом) и проверить, что он вырезан, а реальный курс со ссылкой остался

## 4. Verification

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit` — зелёные
- [x] 4.2 Пересобрать контейнеры и проверить запрос «курсы по js»: вымышленный курс не выводится
- [x] 4.3 `openspec validate recommend-only-catalog-courses --strict` и архивация
