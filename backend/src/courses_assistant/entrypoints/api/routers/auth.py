"""Аутентификация (JSON): вход, регистрация, выход, текущий пользователь."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from courses_assistant.application.commands import RegisterUser
from courses_assistant.container import Container
from courses_assistant.domain.errors import EmailAlreadyExists, InvalidRole
from courses_assistant.domain.security import verify_password
from courses_assistant.entrypoints.api.dependencies import (
    USER_SESSION_KEY,
    get_container,
    get_current_user,
)
from courses_assistant.entrypoints.api.schemas import LoginRequest, MeRead, RegisterRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=MeRead, status_code=201)
async def register(
    payload: RegisterRequest,
    request: Request,
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
    request.session[USER_SESSION_KEY] = user.id
    return MeRead(role=user.role, id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=MeRead)
async def login(
    payload: LoginRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> MeRead:
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_email(payload.email)
        password_hash = (
            await uow.users.get_password_hash(user.id) if user is not None else None
        )
    if user is None or not password_hash or not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    request.session[USER_SESSION_KEY] = user.id
    return MeRead(role=user.role, id=user.id, name=user.name, email=user.email)


@router.post("/logout")
async def logout(request: Request) -> dict[str, str]:
    request.session.pop(USER_SESSION_KEY, None)
    return {"status": "ok"}


@router.get("/me", response_model=MeRead)
async def me(
    request: Request,
    container: Container = Depends(get_container),
) -> MeRead:
    user = await get_current_user(request, container)
    if user is None:
        return MeRead(role=None)
    return MeRead(role=user.role, id=user.id, name=user.name, email=user.email)
