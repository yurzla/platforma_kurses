"""Дашборд: серверный рендер Jinja2-страницы."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    token: str | None = None,
    container: Container = Depends(get_container),
) -> HTMLResponse:
    expected = container.settings.admin_token
    if expected:
        cookie = request.cookies.get("admin_token")
        if token != expected and cookie != expected:
            raise HTTPException(status_code=401, detail="Требуется admin token")

    response = templates.TemplateResponse(
        request,
        "dashboard.html",
        {"token_required": bool(expected)},
    )
    if expected and token == expected:
        response.set_cookie("admin_token", token, httponly=True, samesite="lax")
    return response
