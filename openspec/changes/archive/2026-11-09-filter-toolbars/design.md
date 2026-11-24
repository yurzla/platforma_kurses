# Design

## Web

`dashboard.html`:

- меткам фильтров Jobs добавляются классы `f-status`, `f-session`, `f-search`;
- меткам фильтров чанков добавляются классы `f-course`, `f-source`, `f-search`;
- идентификаторы полей и обработчики не меняются.

`dashboard.css`:

- общее правило для `.filters` задаёт `box-sizing: border-box` и `height: 38px`
  полям, селектам и кнопкам; кнопки становятся `inline-flex` с центрированием,
  `flex: 0 0 auto` и `white-space: nowrap`;
- `#jobs-filters, #chunks-filters` получают `flex-wrap: nowrap`, метки —
  `min-width: 0`, поля — `width: 100%; min-width: 0`;
- ширины меток задаются через `flex-basis`, чтобы сжимался прежде всего селект
  курса;
- `#f-apply, #ch-apply` получают `margin-left: auto`, прижимая пару кнопок вправо;
- `#ch-course` получает `overflow: hidden`, `text-overflow: ellipsis`,
  `white-space: nowrap`;
- на `max-width: 760px` тулбары снова переносятся, метки занимают всю ширину.

Backend, API и JS не меняются.

## Testing

Web-тест проверяет по тексту CSS: общую высоту контролов, `flex-wrap: nowrap`
для Jobs и Чанков, `margin-left: auto` у кнопок и обрезку `#ch-course`.
