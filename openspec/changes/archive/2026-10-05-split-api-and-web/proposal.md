## Why

Сейчас HTML (дашборд, вход) и JSON-API живут в одном FastAPI-приложении, а обучение студентов и тесты вовсе недоступны. Нужно разделить сервисы: API — чистый JSON-бэкенд, web — визуализация, чтобы развивать интерфейсы независимо.

## What Changes

- **BREAKING**: API переносится на порт `5000` и перестаёт отдавать HTML/статику; добавляются JSON-эндпоинты `/api/v1/auth/*` (вход/выход/`me`).
- Появляется отдельный web-сервис `entrypoints/web` на порту `8000` (Jinja2) с прозрачным прокси `/api/*`; cookie сессии пробрасываются.
- Дашборд, вход и статика переносятся в web; на `/login` — переключатель роли «Студент/Администратор».
- Аутентификация остаётся в API; web только редиректит/проксирует.

## Capabilities

### New Capabilities
- `web-interface`: web-сервис визуализации (страницы входа/дашборда/обучения), прокси `/api/*` и проброс cookie.

### Modified Capabilities
- `ops-dashboard`: HTML-страница дашборда отдаётся web-сервисом; вход/выход — JSON-эндпоинты API, форма входа — в web.
- `platform-health`: конфигурация портов (`API_PORT=5000`, `WEB_PORT=8000`) и `API_BASE_URL`; health web-сервиса.

## Impact

- Новый пакет `entrypoints/web` (`app`, `client`, `routers/{pages,proxy}`, `templating`, templates/static).
- API: удалены `routers/dashboard.py`, `templating.py`, `templates/`, `static/`; `auth` переписан на JSON; `entrypoints/middleware.py` — общий.
- Конфиг: `api_port=5000`, `api_base_url`, `web_host`, `web_port`; compose-сервис `web`; `Dockerfile` EXPOSE `5000 8000`.
- Тесты: HTML-тесты перенесены в `tests/web/test_web.py`; API-тесты — на JSON-auth.
- `.env.example`, `README.md`, `AGENTS.md`, `Makefile`.
