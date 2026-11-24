## Why

Подбор курсов в глобальном чате сейчас делает LLM по полному каталогу: модель не перечисляет все
подходящие курсы и иногда выдумывает названия (например, для «какие курсы по js есть?» отдавала
только один курс или придумывала «Супер курс по языку JavaScript»). Нужны рекомендации на основе
эмбеддингов, а не свободного выбора модели.

## What Changes

- Глобальный вопрос про подбор/перечисление курсов обрабатывается **рекомендателем на эмбеддингах**:
  запрос расширяется ключевыми словами (LLM), эмбеддится и сравнивается по cosine с уже
  векторизованными описаниями курсов (`content_chunks.source_type='course_description'`).
- Ответ на такой вопрос — **детерминированный список** найденных опубликованных курсов (название,
  ссылка `/courses/ID`, краткое описание); модель список не сочиняет.
- Отбор кандидатов: `top_k` + относительный `margin` + `min_score` (конфигурируемо).
- Если совпадений нет — прежний grounded-ответ (RAG + каталог).
- Сессии по конкретному курсу рекомендатель не используют.
- `embed_chunks` пере-эмбеддит описание курса при изменении текста.

## Capabilities

### New Capabilities

- `course-recommendations`: подбор курсов платформы по семантической близости к запросу на
  эмбеддингах, с расширением запроса и детерминированным списком результата.

### Modified Capabilities

- `rag-chat`: глобальный вопрос про подбор курсов делегируется рекомендателю; уточняется правило
  фильтрации пунктов со ссылками на неизвестные курсы.

## Impact

- Backend domain: `domain/recommender.py` (новый), `domain/prompts.py`,
  `domain/recommendations.py`.
- Backend application: `application/ports.py`, `application/recommendations.py` (новый),
  `application/handlers.py`.
- Backend adapters: `adapters/persistence/repositories.py`, `adapters/persistence/unit_of_work.py`.
- Настройки: `config.py`, `docker-compose.yml`.
- Скрипты: `scripts/embed_chunks.py`.
- Тесты: domain/application/adapter/integration.
- БД: без миграций (используются существующие `course_description` эмбеддинги).
