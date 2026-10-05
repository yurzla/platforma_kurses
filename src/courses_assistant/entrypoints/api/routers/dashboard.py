"""Дашборд: серверный рендер Jinja2-страницы."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container, require_admin_page
from courses_assistant.entrypoints.api.templating import templates

router = APIRouter(tags=["dashboard"], dependencies=[Depends(require_admin_page)])


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    container: Container = Depends(get_container),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"auth_enabled": container.settings.admin_auth_enabled()},
    )
