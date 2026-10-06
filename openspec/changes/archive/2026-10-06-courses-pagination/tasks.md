## 1. API-пагинация

- [x] 1.1 `entrypoints/api/schemas.py`: `CourseListResponse{items,total,limit,offset}`
- [x] 1.2 `application/ports.py`: `list_courses(..., limit, offset)`, `count_courses(...)`
- [x] 1.3 `adapters/persistence/repositories.py`: `limit/offset` в запросе, `count_courses` с теми же фильтрами
- [x] 1.4 `entrypoints/api/routers/catalog.py`: `limit`/`offset` query, ответ `CourseListResponse`
- [x] 1.5 `tests/fakes.py`: `limit/offset` + `count_courses`

## 2. Web-пагинация и сетка

- [x] 2.1 `routers/pages.py`: `PAGE_SIZE=10`, `page` в `courses` и `my_courses`, чтение конверта, клампинг
- [x] 2.2 `templates/_pagination.html`: стрелки + номера страниц
- [x] 2.3 `templates/courses.html`, `templates/my_courses.html`: подключить пагинацию
- [x] 2.4 `static/web.css`: сетка 2 колонки (1 на ≤700px), стили пагинации

## 3. Тесты

- [x] 3.1 `tests/api/test_catalog.py`: конверт, `limit/offset` + `total`, сочетание с `enrolled`
- [x] 3.2 `tests/web/test_web.py`: 10 на страницу, `?page=2`, отсутствие навигации при одной странице, 2 колонки в CSS

## 4. Документация

- [x] 4.1 `README.md`: строка таблицы API, подраздел с форматом ответа (BREAKING), список web-страниц (`/my-courses`, пагинация)
- [x] 4.2 `AGENTS.md`: заметка о конверте `GET /api/v1/courses`

## 5. Проверка

- [x] 5.1 `make lint`, `make typecheck`, `make test-unit`, `openspec validate courses-pagination --strict`
- [x] 5.2 Пересборка `api` и `web`, e2e-проверка `/courses?page=2`
