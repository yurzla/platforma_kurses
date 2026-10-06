# Clean HTML entities in course descriptions

## Why

В описаниях курсов, загруженных из демо-дампа, остались HTML-сущности (`&nbsp;`, `&gt;`)
и неразрывные пробелы вместо обычных. Поскольку описания рендерятся как простой текст
(с автоэкранированием), пользователь видит их буквально — например, в курсе `id=16`
(«Инди-курс программирования на Python») 25 вхождений `&nbsp;`. Импортёр `load_stepik`
декодирует сущности, но данные из дампа через него не проходили, а `html.unescape` даёт
неразрывный пробел U+00A0, который тоже нужно нормализовать.

## What Changes

- `clean_description` (импортёр): после `html.unescape` нормализует U+00A0 в обычный пробел.
- `clean_text` (импортёр, используется для RAG-чанков): декодирует HTML-сущности; `embed_chunks`
  использует общий `clean_text` вместо своей копии.
- `embed_chunks` получает флаг `--rebuild`; существующие чанки и эмбеддинги пересоздаются из
  очищенного текста.
- Новый идемпотентный скрипт `fix_course_descriptions`, приводящий уже сохранённые описания
  курсов к очищенному виду.
- Так как пересборка чанков меняет их идентификаторы, старая история чатов (ссылающаяся на
  прежние чанки) удаляется вместе со связанными job-ами.
- Образы `api`/`worker`/`web` пересобираются под обновлённый код.
- Демо-дамп `tmp/edu_platform_kurses.sql` перегенерируется из очищенной БД.

## Impact

- `backend/src/courses_assistant/scripts/load_stepik.py`,
  `backend/src/courses_assistant/scripts/embed_chunks.py`,
  новый `backend/src/courses_assistant/scripts/fix_course_descriptions.py`.
- Спека `web-interface` — требование «Formatted course description».
- Тесты `tests/unit/test_load_stepik.py`.
