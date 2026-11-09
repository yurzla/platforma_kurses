# Proposal

## Why

Сводка RAG-индекса показывает только курсы, у которых уже есть чанки. Курсы без
материалов (`Тест1`, `Тест2`, `test`) в таблицу не попадают, а карточка «без
эмбеддинга» считает чанки, а не курсы, поэтому выглядит нулевой. Оператор не
видит курсы, которые вообще не проиндексированы.

## What Changes

- Включать в сводку индекса все курсы, в том числе без чанков, с нулевыми
  счётчиками.
- Добавить в сводку количество курсов без эмбеддингов и без чанков.
- Добавить каждому курсу статус: `ok`, `partial`, `missing_embeddings`, `empty`.
- В админке переименовать карточку в «чанков без эмбеддинга», добавить карточки
  «курсов без эмбеддингов» и «курсов без чанков».
- В таблице «По курсам» добавить колонку «Состояние».
- Разместить «По курсам» под «По типам источников», а не справа.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `ops-dashboard`: сводка RAG-индекса должна покрывать все курсы и показывать их
  состояние по чанкам и эмбеддингам.

## Impact

- `backend/src/courses_assistant/entrypoints/api/routers/admin.py`
- `backend/src/courses_assistant/entrypoints/api/schemas.py`
- `web/src/courses_web/templates/dashboard.html`
- `web/src/courses_web/static/dashboard.js`
- `web/src/courses_web/static/dashboard.css`
- `tests/integration/test_admin_insights.py`
- `tests/web/test_web.py`
