# Design

`dashboard.html`: блок `<section class="cards" id="status-cards">` переносится из
`#panel-diagnostics` в `#diagnostic-jobs` — после описания и перед
`#jobs-filters`.

ID карточек (`status-cards`, `cnt-queued`, `cnt-running`, `cnt-done`,
`cnt-failed`) не меняются:

- обработчики кликов в `dashboard.js` продолжают работать;
- `loadOverview()` по-прежнему вызывается в `refresh()` для всех подвкладок,
  потому что обновляет ещё Streams и метку времени.

CSS не меняется: `.cards` уже подходит для контейнера панели.

## Testing

Web-тест проверяет, что `id="status-cards"` находится внутри панели
`#diagnostic-jobs` и отсутствует в остальных панелях.
