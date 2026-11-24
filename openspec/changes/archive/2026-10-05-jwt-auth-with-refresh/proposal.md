## Why

Сейчас аутентификация держится на серверной session-cookie (`SessionMiddleware`), а часть эндпоинтов API (`chat/ask/jobs`) вообще без авторизации — есть IDOR и чтение чужих сессий/job-ов. Нужен stateless JWT-доступ (access + refresh) с httpOnly-cookie и закрытие незащищённых эндпоинтов с проверкой владения.

## What Changes

- **BREAKING**: сессионная cookie заменяется на JWT. Вход/регистрация выдают пару токенов: short-lived **access JWT** и opaque **refresh**-токен; оба — в httpOnly cookie.
- **BREAKING**: `SESSION_SECRET`/`SESSION_MAX_AGE` заменяются на `JWT_SECRET`/`JWT_ALGORITHM`/`ACCESS_TOKEN_TTL`/`REFRESH_TOKEN_TTL`; cookie `access_token`/`refresh_token`.
- Новый эндпоинт `POST /api/v1/auth/refresh`: читает refresh-cookie, отзывает старый токен (ротация) и выдаёт новую пару; повторное использование отозванного токена отзывает все сессии пользователя.
- Refresh-токены хранятся в PostgreSQL (хеш sha256) с ротацией и отзывом; logout отзывает текущий refresh.
- Роль по-прежнему читается из БД на каждом запросе (в access-токене только `sub`), поэтому смена роли применяется немедленно.
- **BREAKING**: `chat`/`ask`/`jobs` требуют аутентификации и проверки владения сессией; поле `user_id` в `POST /chat/sessions` убирается.
- Web-прокси прозрачно обновляет access по refresh-cookie при `401` (авто-refresh).

## Capabilities

### New Capabilities
- (нет)

### Modified Capabilities
- `user-auth`: вход/регистрация выдают access+refresh JWT; добавлены refresh, ротация и отзыв; текущий пользователь определяется по токену.
- `platform-health`: конфигурация сессии заменена на JWT-настройки (`JWT_SECRET`, TTL, cookie).
- `rag-chat`: создание сессии и чтение истории требуют входа и владения сессией.
- `question-jobs`: постановка вопроса и polling статуса требуют входа и владения сессией.
- `web-interface`: прокси пробрасывает токен и выполняет авто-refresh при `401`.

## Impact

- Backend: `config`, `domain/errors`, `application/ports`, `adapters` (JWT-токены, `SqlRefreshTokenRepository`, ORM, миграция `0006_refresh_tokens`), `entrypoints/api` (dependencies, auth, chat, jobs, app), `container`.
- Web: `client.py`, `routers/proxy.py`, `routers/pages.py` (авто-refresh и ретрансляция cookie).
- БД: новая таблица `refresh_tokens` (Alembic-миграция).
- Зависимости: добавлен `pyjwt`; `itsdangerous` как явная зависимость больше не нужен.
- Инфра/доки: `.env.example`, `docker-compose.yml`, `README.md`, `AGENTS.md`.
