"""Аутентификация (JSON): вход, регистрация, refresh, выход, текущий пользователь."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from courses_assistant.application.commands import RegisterUser
from courses_assistant.container import Container
from courses_assistant.domain.errors import EmailAlreadyExists, InvalidRole, InvalidToken
from courses_assistant.domain.models import User
from courses_assistant.domain.security import (
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from courses_assistant.entrypoints.api.auth_cookies import clear_auth_cookies, set_auth_cookies
from courses_assistant.entrypoints.api.dependencies import (
    extract_access_token,
    get_container,
)
from courses_assistant.entrypoints.api.schemas import LoginRequest, MeRead, RegisterRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


async def _issue_tokens(container: Container, user_id: int) -> tuple[str, str]:
    """Выдаёт access+refresh и сохраняет refresh-хеш в БД."""
    access = container.tokens.create_access_token(user_id)
    refresh = new_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=container.settings.refresh_token_ttl)
    async with container.uow_factory() as uow:
        await uow.refresh_tokens.add(user_id, hash_refresh_token(refresh), expires_at)
    return access, refresh


def _me(user: User) -> MeRead:
    return MeRead(role=user.role, id=user.id, name=user.name, email=user.email)


@router.post("/register", response_model=MeRead, status_code=201)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    container: Container = Depends(get_container),
) -> MeRead:
    try:
        user = await container.handlers.register_user(
            RegisterUser(
                email=payload.email,
                name=payload.name,
                password=payload.password,
                role=payload.role,
            )
        )
    except InvalidRole as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmailAlreadyExists as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    access, refresh = await _issue_tokens(container, user.id)
    set_auth_cookies(response, container.settings, access, refresh)
    return _me(user)


@router.post("/login", response_model=MeRead)
async def login(
    payload: LoginRequest,
    response: Response,
    container: Container = Depends(get_container),
) -> MeRead:
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_email(payload.email)
        password_hash = (
            await uow.users.get_password_hash(user.id) if user is not None else None
        )
    if (
        user is None
        or not password_hash
        or not verify_password(
            payload.password, password_hash, container.settings.require_password_key()
        )
    ):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    access, refresh = await _issue_tokens(container, user.id)
    set_auth_cookies(response, container.settings, access, refresh)
    return _me(user)


@router.post("/refresh", response_model=MeRead)
async def refresh(
    request: Request,
    response: Response,
    container: Container = Depends(get_container),
) -> MeRead:
    raw = request.cookies.get(container.settings.refresh_cookie)
    if not raw:
        raise HTTPException(status_code=401, detail="Нет refresh-токена")
    token_hash = hash_refresh_token(raw)
    now = datetime.now(UTC)
    async with container.uow_factory() as uow:
        token = await uow.refresh_tokens.get(token_hash)
        if token is None:
            raise HTTPException(status_code=401, detail="Недействительный refresh-токен")
        if token.revoked_at is not None:
            await uow.refresh_tokens.revoke_all_for_user(token.user_id, now)
            await uow.commit()
            raise HTTPException(status_code=401, detail="Refresh-токен отозван")
        if token.expires_at <= now:
            raise HTTPException(status_code=401, detail="Refresh-токен истёк")
        user = await uow.users.get(token.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        await uow.refresh_tokens.revoke(token_hash, now)
        access = container.tokens.create_access_token(user.id)
        refresh = new_refresh_token()
        expires_at = now + timedelta(seconds=container.settings.refresh_token_ttl)
        await uow.refresh_tokens.add(user.id, hash_refresh_token(refresh), expires_at)
    set_auth_cookies(response, container.settings, access, refresh)
    return _me(user)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    container: Container = Depends(get_container),
) -> dict[str, str]:
    raw = request.cookies.get(container.settings.refresh_cookie)
    if raw:
        async with container.uow_factory() as uow:
            await uow.refresh_tokens.revoke(hash_refresh_token(raw), datetime.now(UTC))
    clear_auth_cookies(response, container.settings)
    return {"status": "ok"}


@router.get("/me", response_model=MeRead)
async def me(
    request: Request,
    container: Container = Depends(get_container),
) -> MeRead:
    token = extract_access_token(request, container.settings)
    if token is None:
        return MeRead(role=None)
    try:
        user_id = container.tokens.decode_access_token(token)
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail="Недействительный токен") from exc
    async with container.uow_factory() as uow:
        user = await uow.users.get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return _me(user)
