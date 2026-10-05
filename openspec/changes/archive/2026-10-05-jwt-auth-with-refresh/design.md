## Context

Текущая аутентификация — серверная session-cookie (`SessionMiddleware`, ключ `user`=id) и незащищённые `chat/ask/jobs`. Переходим на stateless JWT (access) + stateful refresh в httpOnly cookie, с проверкой владения объектами.

## Decisions

- **Хранилище**: JWT только в httpOnly cookie (`access_token`, `refresh_token`), не в JS. `SameSite=Lax`, `Secure=COOKIE_SECURE`. Access-cookie `Path=/`, refresh-cookie `Path=/` — иначе web-прокси не увидит refresh на `/api/v1/courses`.
- **Access-токен**: JWT HS256, claims `sub` (id), `type=access`, `exp`, `iat`, `jti`. TTL короткий (по умолчанию 15 минут). Роль в токене **не** хранится — читается из БД на каждом запросе (смена роли применяется мгновенно).
- **Refresh-токен**: opaque `secrets.token_urlsafe(32)`, в БД хранится `sha256`-хеш. TTL длинный (по умолчанию 14 дней). Хранение в PostgreSQL (таблица `refresh_tokens`), т.к. нужны надёжные ротация и отзыв, переживающие рестарт.
- **Ротация**: `POST /api/v1/auth/refresh` находит refresh по хешу, проверяет `expires_at`/`revoked_at`, помечает старый `revoked_at=now`, выдаёт новую пару. Повторное использование уже отозванного токена → отзыв всех refresh пользователя и 401 (детект компромисса).
- **Logout**: отзывает текущий refresh и очищает обе cookie. Access остаётся валиден до `exp` (короткий TTL); denylist по `jti` не вводим.
- **Проверка запросов**: `get_current_user` берёт access из cookie **или** `Authorization: Bearer`, декодирует, грузит `User` из БД; ошибки → 401. `require_user`/`require_admin` поверх.
- **Владение**: `chat`/`ask`/`jobs` требуют `require_user`; сессия/job доступны владельцу или `admin`, иначе 403 (чужой) / 404 (нет объекта). Поле `SessionCreate.user_id` удалено — сессия всегда привязывается к текущему пользователю.
- **Web авто-refresh**: web-прокси при `401` от API и наличии refresh-cookie вызывает `/api/v1/auth/refresh`, повторяет исходный запрос с новым access и ретранслирует новые `Set-Cookie` браузеру. Общий httpx-клиент не хранит cookie (уже очищается) — cookie пробрасываются вручную.
- **Конфиг**: `session_secret`→`jwt_secret`; `resolved_session_secret()`→`resolved_jwt_secret()` (пусто → эфемерный + warning). Убрать `session_max_age`. Добавить `jwt_algorithm`, `access_token_ttl`, `refresh_token_ttl`, имена cookie.
- **JWT-кодек**: адаптер `adapters/tokens/jwt.py` + порт `TokenService` в `application/ports.py` (domain остаётся без внешних зависимостей).

## Risks / Trade-offs

- CSRF не закрываем отдельным токеном: cookie-аутентификация + `SameSite=Lax` (мутирующие POST/PATCH межсайтово заблокированы современными браузерами).
- Access после logout живёт до истечения TTL; для мгновенного отзыва нужен denylist (вне объёма).
- Refresh-cookie `Path=/` расширяет её отправку на все пути — компромисс ради авто-refresh в прокси.
- Просроченные refresh копятся; очистка — опционально через cron (вне базового объёма).
- Переход ломает контракт `POST /chat/sessions` (убрано `user_id`) и cookie-имя сессии; и API, и web деплоятся вместе.
