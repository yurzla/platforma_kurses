# Proposal

## Why

Админ-дашборд показывает не все фоновые очереди: dead-letter очередь индексации
(`rag.index.dead`) не видна ни в DLQ, ни в индекс-вкладке, поэтому упавшая индексация курсов и
шагов остаётся незамеченной. Метрики Streams бедны (только length/pending/lag/consumers), из-за
чего нельзя отличить «воркер жив и простаивает» от «воркер упал», а Health не отражает живость
indexer/worker/cron.

## What Changes

- DLQ-эндпоинт и вкладка начинают агрегировать все dead-letter стримы: `rag.dead`,
  `rag.index.dead`, `rag.cron.dead`. В записи добавляется сам dead-stream и фильтр по нему.
- Метрики Streams расширяются: существование стрима, ID последнего сгенерированного и
  доставленного сообщения, время последнего сообщения, список консьюмеров с pending/idle и тип
  стрима (обработочный или DLQ).
- Вкладка «Индекс» получает блок очереди индексации: длина/pending/lag `rag.index.requests` и
  число записей в `rag.index.dead`.
- Health получает блок «Воркеры»: наличие консьюмеров в группах `rag-workers`, `rag-indexers`,
  `rag-cron`.
- Веб-дашборд: колонка «Очередь» и фильтр в DLQ, расширенные колонки Streams с подсветкой
  отставания, карточки очереди индексации, блок воркеров в «Состоянии».

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `ops-dashboard`: dead-letter видимость по всем DLQ-стримам с указанием источника; расширенные
  метрики стримов; блок очереди индексации; живость воркеров в health; соответствующие изменения
  страницы дашборда.

## Impact

- Backend: `application/ports.py`, `adapters/broker/redis_streams.py`,
  `entrypoints/api/routers/admin.py`, `entrypoints/api/schemas.py`, `application/queries.py`.
- Web: `web/src/courses_web/templates/dashboard.html`,
  `web/src/courses_web/static/dashboard.js`, стили дашборда.
- Тесты: `tests/api/test_admin.py`, `tests/fakes.py`, web-smoke.
- Внешние контракты: `GET /api/v1/admin/dlq` (новые поля и фильтр), `GET /api/v1/admin/streams`
  и `/overview` (новые поля), `GET /api/v1/admin/index` (блок `queue`),
  `GET /api/v1/admin/health` (блок `workers`). Обратная совместимость сохраняется: поля
  добавляются, существующие не удаляются.
