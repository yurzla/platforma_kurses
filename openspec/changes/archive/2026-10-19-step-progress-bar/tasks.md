## 1. Data

- [x] 1.1 `routers/pages.py`: прогресс курса на странице шага через `_course_progress`
- [x] 1.2 `routers/pages.py`: кумулятивные контрольные точки модулей (без последней границы)

## 2. Markup and styles

- [x] 2.1 `templates/step.html`: блок прогресса (процент, «Пройдено N из M шагов», шкала, тики)
- [x] 2.2 `static/web.css`: стили `.step-progress` и контрольных точек
- [x] 2.3 `templates/step.html`: `window.STEP_PROGRESS` для клиентского обновления

## 3. Behaviour

- [x] 3.1 `static/web.js`: после успешной отметки обновить счётчик, процент, ширину и `aria-valuenow`

## 4. Tests

- [x] 4.1 Web: процент и подпись прогресса на странице шага
- [x] 4.2 Web: контрольные точки на границах модулей, последняя граница не рисуется
- [x] 4.3 Web: обновление прогресса после отметки шага (проверка в UI)

## 5. Verification

- [x] 5.1 `make lint`, `make typecheck`, `make test`
- [x] 5.2 `openspec validate step-progress-bar --strict`
- [x] 5.3 Пересобрать `web`, проверить бар и обновление после отметки в UI
