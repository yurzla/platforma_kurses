# Design

## Web

`dashboard.html`:

- в `diagnostic-tabs` добавляется кнопка «Чанки» с `data-diagnostic="chunks"`;
- блок с `chunks-filters`, таблицей `chunks-body` и пейджером переносится из
  `#diagnostic-index` в новый `#diagnostic-chunks`;
- `#diagnostic-index` сохраняет карточки, `index-meta`, `index-types-body` и
  `index-courses-body`.

`dashboard.js`:

- `switchDiagnostic` скрывает/показывает `diagnostic-chunks`;
- `loadIndex()` больше не вызывает `loadChunks()` и только рендерит сводку;
- `loadChunksTab()` сначала загружает сводку индекса (для списка курсов), затем
  вызывает `loadChunks()`;
- `refresh()` для `chunks` вызывает `loadChunksTab()`, для `index` — только
  `loadIndex()`.

Backend и API не меняются.

## Testing

Web-тест проверяет наличие подвкладки `Чанки`, панели `diagnostic-chunks` и
таблицы `chunks-body`; отдельно проверяется, что таблица чанков не входит в
разметку панели `diagnostic-index`.
