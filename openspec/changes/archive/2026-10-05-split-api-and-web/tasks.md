## 1. Перенос портов и HTML

- [x] 1.1 `config.py`: `api_port=5000`, `api_base_url`, `web_host`, `web_port`.
- [x] 1.2 Вынести `RequestContextMiddleware` в `entrypoints/middleware.py`.
- [x] 1.3 Удалить из API `routers/dashboard.py`, `templating.py`, `templates/`, `static/`.
- [x] 1.4 Перенести шаблоны/статику в `entrypoints/web`.

## 2. JSON-аутентификация API

- [x] 2.1 `POST /api/v1/auth/admin/login|logout`, `GET /api/v1/auth/me`.
- [x] 2.2 Схемы `AdminLoginRequest`, `StudentLoginRequest`, `MeRead`.
- [x] 2.3 Регистрация роутеров в `api/app.py` без статики/дашборда.

## 3. Web-сервис

- [x] 3.1 `web/app.py` + `__main__.py` (uvicorn, порт `web_port`).
- [x] 3.2 `web/client.py` (проброс cookie, relay `Set-Cookie`).
- [x] 3.3 `web/routers/proxy.py` — `/api/*`.
- [x] 3.4 `web/routers/pages.py` — `/`, `/health`, `/login`, `/logout`, `/dashboard`, `/courses*`.
- [x] 3.5 Шаблоны: `base`, `_topbar`, `login` (переключатель роли), `dashboard`, `courses`, `course`, `step`; статика `web.js`, `web.css`.

## 4. Инфраструктура и документация

- [x] 4.1 `docker-compose.yml`: `api` → 5000, сервис `web` → 8000.
- [x] 4.2 `Dockerfile` EXPOSE `5000 8000`, default port 5000.
- [x] 4.3 `pyproject.toml`: скрипт `courses-assistant-web`.
- [x] 4.4 `.env.example`, `README.md`, `AGENTS.md`, `Makefile`.

## 5. Тесты

- [x] 5.1 `tests/api/test_admin.py` — JSON-auth.
- [x] 5.2 `tests/web/test_web.py` — страницы, вход, прокси, дашборд.
- [x] 5.3 `ruff → mypy → pytest`.
