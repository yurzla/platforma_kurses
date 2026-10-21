# Схема БД `edu_platform_kurses`

PostgreSQL + pgvector. В текущей схеме --- **20 таблиц**: предметные
таблицы учебной платформы и служебные таблицы (`alembic_version`,
`refresh_tokens`, `jobs`, `step_sources`).

Данные курсов импортируются из Stepik с помощью `stepik_dump.py` и
`load_stepik.py`.\
Текстовые материалы подготавливаются для RAG и векторного поиска с
помощью `embed_chunks.py`.

Обозначения:

-   **PK** --- первичный ключ
-   **FK** --- внешний ключ
-   **UQ** --- уникальное значение / ограничение
-   **NN** --- `NOT NULL`

------------------------------------------------------------------------

## 1. Пользователи и учебные предпочтения

### `users`

  Поле             | Тип          | Ключ  |   Описание
  -----------------|--------------|-------|--------------
  `id`             |BIGSERIAL     | PK    |Внутренний ID пользователя
  `email`          | TEXT          |UQ, NN  |Логин / email
  `password_hash`  | TEXT          | NN       | Хеш пароля
  `name`           | TEXT          | NN       | Отображаемое имя
  `role`           | TEXT          | NN       | `student` / `teacher` / `admin`
  `created_at`     | TIMESTAMPTZ   | NN       |Дата регистрации

### `user_learning_preferences`

Хранит явные предпочтения пользователя, используемые рекомендательной
системой.

  Поле                | Тип           | Ключ                | Описание
  ------------------- | ------------- | ------------------- | ---------------------------------------
  `user_id`           |BIGINT        | PK, FK → users.id   | Пользователь
  `interests`         |TEXT          |                    | Интересующие направления и технологии
  `goals`             |TEXT          |                     | Учебные цели пользователя
  `preferred_level`   |TEXT          |                      | Предпочитаемый уровень курса
  `updated_at`        |TIMESTAMPTZ   |NN                    | Дата последнего изменения

Связь с `users`: **1:1**.

### `user_course_wishlist`

Курсы, которые пользователь явно отметил как желаемые к прохождению.

  Поле          | Тип           |Ключ                 | Описание
  -------------- | ------------- | -------------------- | -----------------
  `user_id`      | BIGINT        | PK/FK → users.id     | Пользователь
  `course_id`    | BIGINT        | PK/FK → courses.id   |Курс
  `created_at`   | TIMESTAMPTZ   | NN                   | Дата добавления

Составной ключ / уникальная пара: `(user_id, course_id)`.

### `refresh_tokens`

Токены обновления для аутентифицированных пользовательских сессий.

  Поле          | Тип           | Ключ                | Описание
  -------------- | ------------- | ------------------- | -----------------------------
  `id`          | BIGSERIAL     | PK                  | Идентификатор токена
  `user_id`     | BIGINT        | FK → users.id, NN   | Владелец токена
  `token_hash`  | TEXT          | UQ, NN              | Хеш токена
  `expires_at`  | TIMESTAMPTZ   | NN                  | Время истечения токена
  `revoked_at`  | TIMESTAMPTZ   |                     | Время отзыва; `NULL`, пока токен активен
  `created_at`  | TIMESTAMPTZ   | NN                  | Время выпуска токена

------------------------------------------------------------------------

## 2. Иерархия курса

### `courses`

  Поле             |Тип           | Ключ   | Описание
  ---------------- | ------------- | ------ | ------------------------------------------
  `id`             | BIGSERIAL     | PK     | Внутренний ID
  `external_id`    | BIGINT        | UQ     |`course.id` из Stepik
  `title`          | TEXT          | NN     |Название
  `description`    | TEXT          |        | Описание курса
  `language`       | TEXT          |        | Язык курса, обычно `ru`
  `level`          |TEXT           |        | `beginner` / `intermediate` / `advanced`
  `owner_id`       | BIGINT        | FK → users.id | Автор курса; `NULL` у импортированных системных курсов
  `is_published`   | BOOLEAN       | NN     | Доступен ли курс студентам
  `created_at`     | TIMESTAMPTZ   | NN     | Дата импорта

Курс, созданный преподавателем, сначала является черновиком
(`is_published = false`) и виден только его автору в разделе
«Преподавание». После публикации он становится доступен в общем каталоге.
Импортированные курсы не имеют автора (`owner_id = NULL`) и не могут
редактироваться через кабинет преподавателя.

### `sections`

  Поле          | Тип         | Ключ              | Описание
  ------------- | ----------- | ----------------- | --------------------------
  `id`          | BIGSERIAL   | PK                | ID
  `course_id`   | BIGINT      | FK → courses.id   | Курс
  `position`    | INT         | NN                | Порядок секции
  `title`       | TEXT        | NN                | Название секции / модуля

### `lessons`

  Поле            | Тип         | Ключ               | Описание
  --------------- | ----------- | ------------------ | -----------------------
  `id`            | BIGSERIAL   | PK                 | ID
  `external_id`   | BIGINT      | UQ                 | `lesson.id` из Stepik
  `section_id`    | BIGINT      | FK → sections.id   | Секция
  `title`         | TEXT        | NN                 | Название урока
  `position`      | INT         | NN                 | Порядок внутри секции

### `steps`

  Поле              | Тип               | Ключ              | Описание
  ----------------- | ----------------- | ----------------- | -----------------
  `id`              | BIGSERIAL         | PK                | ID
  `external_id`     |BIGINT             | UQ                | `step.id` из Stepik
  `lesson_id`       | BIGINT            | FK → lessons.id   | Урок
  `position`        | INT               | NN                | Порядок внутри урока
  `step_type`       | TEXT              | NN                | `text` / `video`...
  `is_enabled`      | BOOLEAN           | NN                | Активен ли шаг

------------------------------------------------------------------------

## 3. Содержимое шага

### `step_contents`

  Поле              | Тип               | Ключ              Описание
  ----------------- | ----------------- | ----------------- -------------------
  `id`              | BIGSERIAL         | PK                |
  `step_id`         | BIGINT            | FK → steps.id, NN |Шаг
  `content_type`    | TEXT              |NN                 | Тип содержимого, например `html`
  `body`            | TEXT              |                   | Основной текст `block.text`
  `options`         | JSONB             |                   | Дополнительные данные `block`: `video`, `samples`, `code_templates`, `limits`, `options` и др.

Пример `options` для `code`-шага:

``` json
{
  "samples": [["7\n30", "450"], ["0\n42", "42"]],
  "code_templates": {"python3": "# put your python code here"},
  "limits": {"python3": {"time": 5, "memory": 256}},
  "execution_time_limit": 5,
  "execution_memory_limit": 256
}
```

### `step_sources`

Служебное сохранение исходных данных шага, полученных из внешнего источника
(например, Stepik). Для каждого шага допускается не более одной записи.

  Поле          | Тип           | Ключ                | Описание
  -------------- | ------------- | ------------------- | ----------------------------------
  `id`          | BIGSERIAL     | PK                  | Идентификатор записи
  `step_id`     | BIGINT        | UQ, FK → steps.id, NN | Шаг
  `source_type` | TEXT          | NN                  | Тип источника; по умолчанию `step-source`
  `payload`     | JSONB         |                     | Исходные данные источника
  `fetched_at`  | TIMESTAMPTZ   | NN                  | Время получения данных

### `choice_question_metadata`

Дополнительные сведения об импортированном вопросе с вариантами ответа.
Одна запись соответствует одному шагу типа `choice`.

  Поле                   | Тип           | Ключ                 | Описание
  -----------------------| ------------- | -------------------- | --------------------------------------
  `step_id`              | BIGINT        | PK, FK → steps.id    | Шаг с вопросом
  `source_question_html` | TEXT          | NN                   | Формулировка вопроса из JSON-источника
  `source_file`          | TEXT          | NN                   | Имя JSON-файла, из которого выполнен импорт
  `needs_review`         | BOOLEAN       | NN                   | Требует ли проверка предложенного ответа
  `is_multiple_choice`   | BOOLEAN       | NN                   | Разрешён ли выбор нескольких вариантов
  `imported_at`          | TIMESTAMPTZ   | NN                   | Время импорта

### `step_choice_options`

Варианты ответа на вопрос типа `choice`. Варианты извлекаются по `step_id` и
сортируются по `position`; модель допускает несколько правильных вариантов.

  Поле                     | Тип           | Ключ                 | Описание
  -------------------------| ------------- | -------------------- | --------------------------------------
  `id`                     | BIGSERIAL     | PK                   | Идентификатор варианта
  `step_id`                | BIGINT        | FK → steps.id, NN    | Шаг с вопросом
  `position`               | INT           | UQ со `step_id`, NN  | Позиция варианта в исходном JSON, с нуля
  `option_html`            | TEXT          | NN                   | Текст или HTML варианта ответа
  `is_suggested_correct`   | BOOLEAN       | NN                   | Предложенный JSON правильный вариант
  `is_correct`             | BOOLEAN       |                      | Подтверждённая правильность; `NULL` до проверки
  `created_at`             | TIMESTAMPTZ   | NN                   | Время импорта

В текущем дампе все варианты проверены: `needs_review = false`, а
`is_correct` заполнен значениями `true` или `false` для каждого варианта.
Существующие вопросы импортируются как одиночный выбор; для вопросов с
несколькими верными ответами `is_multiple_choice` нужно явно установить в `true`
и отметить все правильные строки в `step_choice_options`.

------------------------------------------------------------------------

## 4. RAG и векторный поиск

### `content_chunks`

Текстовые фрагменты, подготовленные для семантического поиска.

  Поле              | Тип               | Ключ              | Описание
  ----------------- | ----------------- | ----------------- | -----------------------
  `id`              |BIGSERIAL          | PK                |
  `course_id`       | BIGINT            | FK → courses.id   | Курс; используется для ограничения RAG текущим курсом
  `lesson_id`       | BIGINT            | FK → lessons.id   | Может быть `NULL`
  `step_id`         | BIGINT            | FK → steps.id     | Может быть `NULL`
  `chunk_text`      | TEXT              |NN                 | Текст фрагмента
  `chunk_index`     | INT               | NN                | Номер фрагмента внутри исходного материала
  `source_type`     |TEXT               | NN                | Фактически используются `theory`, `task`, `course_description`; архитектура допускает также другие типы, например `video` `faq`
  `created_at`      |TIMESTAMPTZ       | NN                | Дата создания

`course_description` используется отдельно для семантического поиска курсов в рекомендательной системе.

### `chunk_embeddings`

  Поле              | Тип               | Ключ                | Описание
  ----------------- | -----------------  | ------------------- | --------------------
  `id`              |BIGSERIAL         |PK                  |
  `chunk_id`        |BIGINT            |FK → content_chunks.id, NN | Векторизованный фрагмент
  `model_name`      |TEXT              | NN                  |`nomic-embed-text`
  `embedding`       | VECTOR(768)        |                  | Вектор размерности 768
  `created_at`      | TIMESTAMPTZ       | NN                  |Дата создания

Текущая embedding-модель: **`nomic-embed-text` через Ollama**.

Для поиска используется оператор pgvector `<=>`, то есть **cosine distance**:

``` sql
ORDER BY ce.embedding <=> %s::vector
```

Чем меньше `distance`, тем семантически ближе векторы. Косинусное сходство связано с этой величиной как:

``` text
cosine_similarity = 1 - cosine_distance
```

------------------------------------------------------------------------

## 5. Чат с LLM

### `chat_sessions`

  Поле             | Тип               | Ключ             | Описание
  -----------------|----------------- | ----------------- | -----------------
  `id`             | BIGSERIAL         | PK                |
  `user_id`         | BIGINT            | FK → users.id    | Пользователь
  `course_id`       | BIGINT            |FK → courses.id    | Текущий курс; может быть `NULL` для общего чата
  `started_at`      | TIMESTAMPTZ       | NN                |Начало сессии
  

### `chat_messages`

  Поле              | Тип               | Ключ               | Описание
  ----------------- | ----------------- | ------------------ | -----------------
  `id`              | BIGSERIAL         | PK                 |
  `session_id`      | BIGINT            |FK → chat_sessions.id |Сессия   
  `role`            | TEXT              |NN                 | `user`, `assistant`, `system`
  `content`         |TEXT              |NN                 |Текст сообщения
  `sources`         | JSONB             |                   | Использованные RAG-источники, сейчас сохраняются`chunk_id`
  `used_chunk_ids`  | JSONB             |                   | Список `content_chunks.id`, использованных в ответе
  `created_at`      |TIMESTAMPTZ       |NN                 |Дата сообщения
  
В новой архитектуре `used_chunk_ids` заполняется при сохранении ответа
ассистента, а `sources`
хранит те же данные в виде словарей-источников.

### `jobs`

Фоновые задания на обработку вопроса в чат-сессии.

  Поле                 | Тип           | Ключ                       | Описание
  ---------------------| ------------- | -------------------------- | -----------------------------------
  `id`                 | TEXT          | PK                         | Идентификатор задания
  `session_id`         | BIGINT        | FK → chat_sessions.id, NN  | Связанная чат-сессия
  `status`             | TEXT          | NN                         | Статус; по умолчанию `queued`
  `question`           | TEXT          | NN                         | Исходный вопрос
  `answer`             | TEXT          |                            | Ответ после обработки
  `sources`            | JSONB         |                            | Использованные источники
  `rewritten_question` | TEXT          |                            | Переформулированный запрос
  `error`              | TEXT          |                            | Текст ошибки при неудаче
  `attempts`           | INT           | NN                         | Число попыток; по умолчанию `0`
  `message_id`         | TEXT          |                            | Идентификатор связанного сообщения
  `created_at`         | TIMESTAMPTZ   | NN                         | Время создания
  `updated_at`         | TIMESTAMPTZ   | NN                         | Время последнего обновления
  
История чата хранится как обычные структурированные данные и извлекается SQL-запросами. Embeddings для истории диалога сейчас не создаются.

------------------------------------------------------------------------

## 6. Обучение и прогресс

### `enrollments`

Связывает пользователя с курсом и хранит общий прогресс прохождения.

  Поле                | Тип            |Ключ              |Описание
  -------------------- | -------------- | ----------------- | -----------------------------------------
  `id`                | BIGSERIAL      |PK                |
  `user_id`           | BIGINT         |FK → users.id     |Пользователь
  `course_id`         | BIGINT         |FK → courses.id   |Курс
  `enrolled_at`       | TIMESTAMPTZ    |NN                |Дата записи
  `progress_percent`  | NUMERIC(5,2)   |NN                |Прогресс от 0 до 100
  `status`            | TEXT           |NN                |`in_progress` / `completed` / `dropped`

Ограничения:

-   UQ: `(user_id, course_id)`;
-   `progress_percent` должен находиться в диапазоне `0..100`;
-   `status` принимает значения `in_progress`, `completed`, `dropped`.

### `user_step_progress`

Детальный прогресс пользователя по отдельным шагам курса.

  Поле                |Тип               |Ключ              |Описание
  ------------------- |----------------- |----------------- |-----------------
  `id`                |BIGSERIAL         |PK                |
  `user_id`           |BIGINT            |FK → users.id     |Пользователь
  `step_id`           |BIGINT            |FK → steps.id     |Шаг
  `status`            |TEXT              |NN                |`not_started`, `in_progress`, `passed` , `failed`
  `best_score`        |NUMERIC(6,2)      |NN                |Лучший результат
  `attempts_count`    |INT               |NN                |Число попыток
  `last_attempt_at`   |TIMESTAMPTZ        |                 |Последняя попытка

UQ: `(user_id, step_id)`.

Эти данные используются для анализа учебной траектории и выявления шагов, потребовавших нескольких попыток или имеющих низкий результат.

------------------------------------------------------------------------

## 7. Служебные таблицы

### `alembic_version`

Служебная таблица Alembic, в которой хранится текущая версия миграции.

  Поле          | Тип                    | Ключ    | Описание
  -------------- | ---------------------- | ------- | -----------------------
  `version_num`  | VARCHAR(32)            | PK, NN  | Идентификатор миграции

------------------------------------------------------------------------

## 8. Использование данных AI-модулями

В проекте разделяются **структурированные данные** и **текстовые знания**.

### Данные, для которых embeddings не нужны

Извлекаются точными SQL-запросами:

-   пользователь и роль --- `users`;
-   интересы и цели --- `user_learning_preferences`;
-   wishlist --- `user_course_wishlist`;
-   текущие, завершённые и брошенные курсы --- `enrollments`;
-   прогресс и результаты по шагам --- `user_step_progress`;
-   история диалогов --- `chat_sessions`, `chat_messages`.

### RAG-ассистент по текущему курсу

``` text
вопрос пользователя
        ↓
при необходимости query rewriting с учетом истории
        ↓
nomic-embed-text
        ↓
embedding вопроса VECTOR(768)
        ↓
pgvector: cosine distance по chunk_embeddings
        ↓
TOP фрагментов текущего course_id
        ↓
контекст + исходный вопрос + история
        ↓
GigaChat-2
        ↓
ответ
```

При RAG-поиске используются прежде всего `content_chunks` типов `theory` и `task`. `course_description` из этого поиска исключается.

### Рекомендательная система

``` text
user_learning_preferences
(interests + goals + preferred_level)
        ↓
формирование поискового текста
        ↓
nomic-embed-text
        ↓
embedding VECTOR(768)
        ↓
сравнение с course_description
        ↓
семантически подходящие курсы
        +
SQL-факты:
enrollments + wishlist + user_step_progress
        ↓
GigaChat-2
        ↓
персональные рекомендации
```

Embedding пользовательского профиля сейчас вычисляется при запросе и отдельно в БД не хранится.

### Подбор курсов в чате

``` text
вопрос про курсы (глобальная сессия)
        ↓
LLM-расширение запроса (ключевые слова/синонимы, temperature 0)
        ↓
nomic-embed-text → embedding вопроса VECTOR(768)
        ↓
pgvector: cosine distance по course_description (chunk_embeddings)
        ↓
отбор: top_k + относительный margin + min_score (только published)
        ↓
детерминированный список курсов (название + ссылка /courses/ID + описание)
        ↓
сохранение ответа (без генерации списка моделью)
```

Если совпадений нет — обычный grounded-ответ (RAG по `theory`/`task` + каталог). Сессии,
привязанные к курсу, рекомендатель не используют. Пере-эмбеддинг описания выполняется
`embed_chunks` при изменении текста.

------------------------------------------------------------------------

## 9. Связи между таблицами

``` text
users ─────── 1:1 ─────── user_learning_preferences

users ──< enrollments >── courses
users ──< user_course_wishlist >── courses

users ──< user_step_progress >── steps

users ──< chat_sessions >── courses
chat_sessions ──< chat_messages
chat_sessions ──< jobs

users ──< refresh_tokens

courses ──< sections ──< lessons ──< steps ──< step_contents
                                          └──< step_sources
                                          └── 1:1 choice_question_metadata
                                          └──< step_choice_options
   │
   └──< content_chunks ──< chunk_embeddings

content_chunks.id
   └── chat_messages.sources (JSONB, логическая ссылка на использованные chunk_id)
```
