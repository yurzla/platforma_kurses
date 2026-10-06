## Why

Списки курсов (`/courses` и `/my-courses`) отдают и рисуют сразу все курсы, без разбивки на страницы, а сетка рассчитана на 3 колонки. При росте каталога страницы становятся длинными и тяжёлыми.

## What Changes

- **BREAKING**: `GET /api/v1/courses` меняет контракт — вместо массива возвращает конверт `{items,total,limit,offset}` с query-параметрами `enrolled`, `limit` (1–200, по умолчанию 50) и `offset`; поведение без параметров (весь каталог) сохраняется через `total`, но потребители обязаны читать `items`.
- Web-страницы `/courses` и `/my-courses` показывают по 10 курсов, добавляются управление страницами (номера + стрелки) и пустая выдача при переходе за границы.
- Сетка карточек курсов — 2 колонки на десктопе, 1 колонка на узких экранах.
- README и OpenSpec описывают новый контракт и помечают изменение как ломающее.

## Capabilities

### New Capabilities

### Modified Capabilities
- `learning-catalog`: «Course catalog» — постраничная выдача `{items,total,limit,offset}`, параметры `limit`/`offset`, сохранён фильтр `enrolled`.
- `web-interface`: ADDED «Course list pagination and layout» — списки курсов по 10 с навигацией, сетка 2 колонки.

## Impact

- Backend: `entrypoints/api/schemas.py`, `application/ports.py`, `adapters/persistence/repositories.py`, `entrypoints/api/routers/catalog.py`.
- Web: `routers/pages.py`, `templates/_pagination.html`, `templates/courses.html`, `templates/my_courses.html`, `static/web.css`.
- Тесты: `tests/fakes.py`, `tests/api/test_catalog.py`, `tests/web/test_web.py`.
- Документация: `README.md`, `AGENTS.md`.
- Схема БД не меняется; Swagger обновляется автоматически из `CourseListResponse`.
