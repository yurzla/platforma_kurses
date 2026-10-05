## 1. Конфигурация

- [x] 1.1 Добавить `admin_username`, `admin_password`, `admin_session_secret`, `admin_cookie_secure`, `admin_session_max_age`; методы `admin_auth_enabled`, `verify_admin`, `session_secret` — проверка: `tests/unit/test_config.py`
- [x] 1.2 Добавить зависимости `itsdangerous`, `python-multipart` — проверка: `uv sync` и импорт

## 2. Аутентификация

- [x] 2.1 Роутер `auth`: `GET /login`, `POST /login`, `POST /logout` с защитой `next` — проверка: `tests/api/test_admin.py`
- [x] 2.2 `SessionMiddleware` в `app.py`; `dependencies.py`: `require_admin` (401), `require_admin_page` (редирект), `admin_authenticated` — проверка: API-тесты
- [x] 2.3 Дашборд под `require_admin_page`; JS редиректит на `/login` при 401 — проверка: `tests/api/test_admin.py`

## 3. Шаблоны и документация

- [x] 3.1 `login.html`, кнопка выхода в `dashboard.html` — проверка: рендер страницы входа/дашборда
- [x] 3.2 Обновить `.env.example`, `docker-compose.yml`, `README.md` (убрать `ADMIN_TOKEN`) — проверка: `docker compose config -q`

## 4. Верификация

- [x] 4.1 `ruff`, `mypy`, `pytest -m "not integration"` — проверка: зелёные
- [x] 4.2 Compose smoke: `/dashboard` → редирект на `/login`, вход, доступ, выход — проверка: ручной прогон
