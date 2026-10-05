## Why

Доступ к дашборду и админ-API защищался единым `ADMIN_TOKEN`, который приходится передавать в URL/заголовке и держать в открытом виде. Нужен привычный вход по логину и паролю с сессией.

## What Changes

- Аутентификация админки/дашборда переводится с `ADMIN_TOKEN` на **логин + пароль** (`ADMIN_USERNAME`/`ADMIN_PASSWORD`).
- Добавляются страница `/login` и `POST /login` (форма), `POST /logout`.
- Вход выдаёт подписанную session-cookie (Starlette `SessionMiddleware`); доступ к `/dashboard` и `/api/v1/admin/*` проверяется по сессии.
- Для HTML-страниц без сессии — редирект на `/login?next=…`; для API — `401`.
- `ADMIN_TOKEN` **удаляется**.

## Capabilities

### New Capabilities
<!-- нет -->

### Modified Capabilities
- `ops-dashboard`: требование «Optional admin access token» заменяется на вход по логину/паролю; добавляются требование о сессии/выходе и сценарии редиректа.
- `platform-health`: в «Configuration from environment» добавляются admin-переменные (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET`, `ADMIN_COOKIE_SECURE`).

## Impact

- Конфиг: `admin_username`, `admin_password`, `admin_session_secret`, `admin_cookie_secure`, `admin_session_max_age`; методы `admin_auth_enabled`, `verify_admin`, `session_secret`.
- Новый роутер `auth`; `SessionMiddleware` в `app.py`; `dependencies.py` (`require_admin`, `require_admin_page`, `admin_authenticated`).
- Шаблон `login.html`; зависимость `itsdangerous` (и `python-multipart` для формы).
- Тесты API/конфига; `.env.example`, `docker-compose.yml`, `README.md`.
