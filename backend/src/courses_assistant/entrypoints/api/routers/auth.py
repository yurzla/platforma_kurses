"""Аутентификация (JSON): администратор и студент."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from courses_assistant.container import Container
from courses_assistant.domain.security import verify_password
from courses_assistant.entrypoints.api.dependencies import (
    ADMIN_SESSION_KEY,
    STUDENT_SESSION_KEY,
    get_container,
)
from courses_assistant.entrypoints.api.schemas import (
    AdminLoginRequest,
    MeRead,
    StudentLoginRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/admin/login", response_model=MeRead)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> MeRead:
    settings = container.settings
    if not settings.admin_auth_enabled():
        return MeRead(role="admin", name="open")
    if not settings.verify_admin(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    request.session[ADMIN_SESSION_KEY] = payload.username
    return MeRead(role="admin", name=payload.username)


@router.post("/admin/logout")
async def admin_logout(request: Request) -> dict[str, str]:
    request.session.pop(ADMIN_SESSION_KEY, None)
    return {"status": "ok"}


@router.post("/student/login", response_model=MeRead)
async def student_login(
    payload: StudentLoginRequest,
    request: Request,
    container: Container = Depends(get_container),
) -> MeRead:
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_email(payload.email)
        if user is None or user.role != "student":
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        password_hash = await uow.users.get_password_hash(user.id)
    if not password_hash or not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    request.session[STUDENT_SESSION_KEY] = user.id
    request.session.pop(ADMIN_SESSION_KEY, None)
    return MeRead(role="student", id=user.id, name=user.name, email=user.email)


@router.post("/student/logout")
async def student_logout(request: Request) -> dict[str, str]:
    request.session.pop(STUDENT_SESSION_KEY, None)
    return {"status": "ok"}


@router.get("/me", response_model=MeRead)
async def me(request: Request, container: Container = Depends(get_container)) -> MeRead:
    settings = container.settings
    if request.session.get(ADMIN_SESSION_KEY) or (
        not settings.admin_auth_enabled() and not request.session.get(STUDENT_SESSION_KEY)
    ):
        name = request.session.get(ADMIN_SESSION_KEY) or "open"
        return MeRead(role="admin", name=name)

    user_id = request.session.get(STUDENT_SESSION_KEY)
    if user_id is not None:
        async with container.uow_factory() as uow:
            user = await uow.users.get(int(user_id))
        if user is not None:
            return MeRead(role="student", id=user.id, name=user.name, email=user.email)
    return MeRead(role=None)
