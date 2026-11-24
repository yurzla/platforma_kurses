## 1. Fix

- [x] 1.1 `client.py`: `call_api` подставляет `request.state.merged_cookie` в заголовки
- [x] 1.2 Проверить, что прокси и обычные вызовы не регрессировали

## 2. Tests

- [x] 2.1 Web: страница шага с испорченным access-токеном рендерит прогресс и навигацию

## 3. Verification

- [x] 3.1 `make lint`, `make typecheck`, `make test`
- [x] 3.2 `openspec validate web-refresh-cookie-propagation --strict`
- [x] 3.3 Пересобрать `web`, проверить страницу шага с истёкшим токеном
