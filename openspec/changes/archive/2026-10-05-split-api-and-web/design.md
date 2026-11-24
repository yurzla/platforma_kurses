## Context

Одно FastAPI-приложение совмещало JSON API и HTML (дашборд, вход). Требуется разделение на два сервиса с общей авторизацией, живущей в API.

## Goals / Non-Goals

- Goals: API — чистый JSON; web — только визуализация; session-cookie не парсится в web; порты API 5000 / web 8000.
- Non-Goals: самостоятельная сессия в web; серверный рендеринг, требующий прямой доступ web к БД.

## Decisions

- **Web как BFF-прокси**: web использует общий `httpx.AsyncClient` (base_url = `API_BASE_URL`) и проксирует `/api/*`; на страницах вручную вызывает API, пробрасывая cookie из запроса. Это исключает дублирование правил авторизации.
- **Auth в API**: JSON-эндпоинты `/api/v1/auth/{admin,student}/{login,logout}` и `/me`. Web-форма `/login` различает роль и вызывает нужный эндпоинт, релеет `Set-Cookie` браузеру.
- **Общий middleware**: `RequestContextMiddleware` вынесен в `entrypoints/middleware.py`.
- **Порты**: `api_port=5000`, `web_port=8000`, `api_base_url` в `Settings`; compose добавляет сервис `web`, зависящий от health API.

## Risks / Trade-offs

- Двойной HTTP-хоп (browser → web → api) добавляет задержку, но упрощает разделение.
- Прокси должен корректно пробрасывать несколько `Set-Cookie`; реализовано через `headers.get_list("set-cookie")`.
- Content-Type формы входа не должен пробрасываться при JSON-вызове API (иначе 422) — заголовок пробрасывается только для raw-прокси.
