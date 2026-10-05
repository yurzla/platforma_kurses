"""Аутентификация админки/дашборда: вход по логину и паролю."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import SESSION_KEY, get_container
from courses_assistant.entrypoints.api.templating import templates

router = APIRouter(tags=["auth"])


def _safe_next(value: str | None) -> str:
    """Защита от open-redirect: разрешаем только локальные пути."""
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/dashboard"
    return value


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/dashboard",
    container: Container = Depends(get_container),
) -> Response:
    settings = container.settings
    if not settings.admin_auth_enabled():
        return RedirectResponse("/dashboard", status_code=303)
    if request.session.get(SESSION_KEY):
        return RedirectResponse(_safe_next(next), status_code=303)
    return templates.TemplateResponse(
        request, "login.html", {"next": _safe_next(next)}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    next: str = Form("/dashboard"),
    container: Container = Depends(get_container),
) -> Response:
    settings = container.settings
    if not settings.admin_auth_enabled():
        return RedirectResponse("/dashboard", status_code=303)
    if not settings.verify_admin(username, password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "next": _safe_next(next),
                "error": "Неверный логин или пароль",
                "username": username,
            },
            status_code=401,
        )
    request.session[SESSION_KEY] = username
    return RedirectResponse(_safe_next(next), status_code=303)


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
