## 1. OpenSpec

- [x] 1.1 Изменение `jwt-auth-with-refresh` создано и валидно (`validate --strict`).

## 2. Конфиг и зависимости

- [x] 2.1 `backend/pyproject.toml`: добавить `pyjwt`, убрать явный `itsdangerous`.
- [x] 2.2 `config.py`: `jwt_secret`/`resolved_jwt_secret`, `jwt_algorithm`, `access_token_ttl`, `refresh_token_ttl`, имена cookie; убрать session-поля.
- [x] 2.3 `.env.example`, `docker-compose.yml`, `README.md`, `AGENTS.md`.

## 3. Токены и БД

- [x] 3.1 `adapters/tokens/jwt.py` + порт `TokenService`; ошибка `InvalidToken`.
- [x] 3.2 `RefreshTokenORM` + миграция `0006_refresh_tokens`.
- [x] 3.3 Порт `RefreshTokenRepository`, SQL-реализация, UoW, фейк.

## 4. API auth

- [x] 4.1 Cookie-хелперы (`set_auth_cookies`/`clear_auth_cookies`).
- [x] 4.2 `dependencies.py`: `get_current_user` из cookie/Bearer, загрузка из БД.
- [x] 4.3 `routers/auth.py`: login/register выдают токены; `POST /refresh` (ротация); logout отзывает и чистит.
- [x] 4.4 `app.py`: удалить `SessionMiddleware`.
- [x] 4.5 `container.py`: wiring `TokenService`.

## 5. Защита chat/jobs

- [x] 5.1 `routers/chat.py`: `require_user`, убрать `payload.user_id`, проверка владения.
- [x] 5.2 `routers/jobs.py`: `require_user` + проверка владения.
- [x] 5.3 `schemas.py`: убрать `user_id` из `SessionCreate`.

## 6. Web авто-refresh

- [x] 6.1 `client.py`: проброс cookie/Bearer, refresh при 401, ретрансляция cookie.
- [x] 6.2 `routers/proxy.py`: авто-refresh и ретрансляция новых cookie.
- [x] 6.3 `routers/pages.py`: ретрансляция новых cookie при SSR-запросах.

## 7. Тесты

- [x] 7.1 Unit: JWT-кодек (exp/tamper/type).
- [x] 7.2 API: login/register/me/refresh/logout; chat/jobs 401/403/404.
- [x] 7.3 Web: авто-refresh, изоляция сессий.
- [x] 7.4 `fakes.py` и обновление существующих тестов.

## 8. Проверка и архив

- [x] 8.1 `ruff → mypy → pytest` (+ integration), сборка образов, compose-smoke.
- [x] 8.2 `openspec archive jwt-auth-with-refresh -y`; `openspec validate --all --strict`.
