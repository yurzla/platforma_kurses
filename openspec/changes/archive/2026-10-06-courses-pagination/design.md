## Context

См. `proposal.md`. `GET /api/v1/courses` (`catalog.py::list_courses`) возвращает `list[CourseSummaryRead]`; в репозитории уже есть фильтр `enrolled_only` (см. `my-courses-page`). В API есть готовый паттерн постраничности (`admin.py::users/jobs`): `limit`/`offset` + конверт `{items,total,limit,offset}`. Web-страницы читают список напрямую из `resp.json()`, карточки вынесены в `_course_cards.html`, сетка `.course-grid` — `repeat(auto-fill, minmax(300px,1fr))`.

## Goals / Non-Goals

**Goals:**
- Серверная пагинация каталога с конвертом и полем `total`.
- Единый вид пагинации на `/courses` и `/my-courses` (10 на страницу).
- Сетка карточек в 2 колонки.

**Non-Goals:**
- Изменение схемы БД и модели `CourseSummaryRead`.
- Сортировка/фильтры каталога (кроме существующих `enrolled`).
- Пагинация страницы шага или истории чата.

## Decisions

- **Конверт `CourseListResponse{items,total,limit,offset}`** вместо массива — единообразие с admin-эндпоинтами; **BREAKING** для внешних клиентов. Миграция: читать `items`.
- **Два метода репозитория** `list_courses(..., limit, offset)` и `count_courses(...)` (как `UserRepository.list/count`), фильтры (`is_published`, `enrolled_only`) общие. Альтернатива (возврат кортежа из одного метода) отклонена ради симметрии с `UserRepository`.
- **Дефолт `limit=50`, `le=200`** как в admin; web явно передаёт `limit=10`. Так API остаётся универсальным, а размер страницы — забота web.
- **`page` в web**, `limit/offset` в API: `offset=(page-1)*10`; `pages=ceil(total/limit)`; `page` клампится к `[1, max(pages,1)]`.
- **Один партиал `_pagination.html`** (номера + стрелки, окно вокруг текущей с первой/последней) для обеих страниц; `base_path` — `/courses` или `/my-courses`.
- **Сетка** `repeat(2, minmax(0,1fr))`; `@media (max-width:700px)` — 1 колонка.

## Risks / Trade-offs

- [Ломающий контракт] → отражено в README/AGENTS и в proposal как BREAKING; внутри репозитория единственный потребитель — web, обновляется в том же изменении.
- [Пустая страница при `page` за пределами] → клампинг номера страницы в роутере.
- [Много страниц в навигации] → окно вокруг текущей + первая/последняя с `…`.

## Migration Plan

1. Обновить web-роуты на чтение `items/total` (в этом же коммите).
2. Внешним клиентам API — перейти с массива на `data["items"]`.
3. Откат — предыдущая версия кода; данные не меняются.

## Open Questions

Нет.
