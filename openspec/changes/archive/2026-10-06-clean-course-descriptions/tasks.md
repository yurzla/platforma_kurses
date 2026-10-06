## 1. Импортёр

- [x] 1.1 `load_stepik.clean_description`: нормализация U+00A0 → пробел после `html.unescape`
- [x] 1.2 `load_stepik.clean_text`: декодирование HTML-сущностей

## 2. Данные

- [x] 2.1 Новый скрипт `fix_course_descriptions`: очистка существующих описаний курсов
- [x] 2.2 Прогон скрипта на БД, проверка отсутствия сущностей/U+00A0
- [x] 2.4 `embed_chunks`: общий `clean_text` + флаг `--rebuild`
- [x] 2.5 Переэмбеддинг (`--rebuild`), проверка отсутствия сущностей/U+00A0 в чанках
- [x] 2.6 Удалить старые чаты (`jobs` + `chat_sessions`, `chat_messages` каскадом)
- [x] 2.7 Пересобрать образы `api`/`worker`/`web`
- [x] 2.3 Перегенерировать `tmp/edu_platform_kurses.sql` из очищенной БД

## 3. Тесты и спека

- [x] 3.1 `tests/unit/test_load_stepik.py`: `&gt;`, `&nbsp;`, отсутствие U+00A0/сущностей в `clean_description` и `clean_text`
- [x] 3.2 delta `web-interface`: MODIFIED «Formatted course description»

## 4. Проверка

- [x] 4.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate clean-course-descriptions --strict`
- [x] 4.2 Пересборка `web`, e2e-проверка курса 16 и карточек