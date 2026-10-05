"""HTML-страницы web-сервиса (Jinja2 поверх JSON API)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from courses_web.client import call_api, relay_cookies
from courses_web.templating import templates

router = APIRouter(tags=["pages"])


def _safe_next(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//"):
        return fallback
    return value


async def _me(request: Request) -> dict[str, Any]:
    resp = await call_api(request, "GET", "/api/v1/auth/me")
    if resp.status_code != 200:
        return {"role": None}
    return resp.json()


@router.get("/")
async def index() -> RedirectResponse:
    return RedirectResponse("/courses", status_code=303)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, role: str = "student", next: str = "") -> Response:
    if role not in ("student", "admin"):
        role = "student"
    return templates.TemplateResponse(
        request, "login.html", {"role": role, "next": next, "me": {"role": None}}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request) -> Response:
    form = await request.form()
    role = str(form.get("role", "student"))
    if role not in ("student", "admin"):
        role = "student"
    next_url = _safe_next(form.get("next"), "/dashboard" if role == "admin" else "/courses")
    password = str(form.get("password", ""))

    if role == "admin":
        api_path = "/api/v1/auth/admin/login"
        payload = {"username": str(form.get("username", "")), "password": password}
    else:
        api_path = "/api/v1/auth/student/login"
        payload = {"email": str(form.get("email", "")), "password": password}

    upstream = await call_api(request, "POST", api_path, json=payload)
    if upstream.status_code == 200:
        response = RedirectResponse(next_url, status_code=303)
        relay_cookies(response, upstream)
        return response

    context = {
        "role": role,
        "next": next_url,
        "error": "Неверный логин или пароль",
        "email": str(form.get("email", "")),
        "username": str(form.get("username", "")),
        "me": {"role": None},
    }
    return templates.TemplateResponse(request, "login.html", context, status_code=401)


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    admin = await call_api(request, "POST", "/api/v1/auth/admin/logout")
    student = await call_api(request, "POST", "/api/v1/auth/student/logout")
    response = RedirectResponse("/login", status_code=303)
    relay_cookies(response, admin)
    relay_cookies(response, student)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    me = await _me(request)
    if me.get("role") != "admin":
        return RedirectResponse("/login?role=admin&next=/dashboard", status_code=303)
    return templates.TemplateResponse(request, "dashboard.html", {"me": me})


@router.get("/courses", response_class=HTMLResponse)
async def courses(request: Request) -> Response:
    resp = await call_api(request, "GET", "/api/v1/courses")
    if resp.status_code == 401:
        return RedirectResponse("/login?next=/courses", status_code=303)
    me = await _me(request)
    return templates.TemplateResponse(
        request,
        "courses.html",
        {"me": me, "courses": resp.json() if resp.status_code == 200 else []},
    )


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course(request: Request, course_id: int) -> Response:
    resp = await call_api(request, "GET", f"/api/v1/courses/{course_id}")
    if resp.status_code == 401:
        return RedirectResponse(f"/login?next=/courses/{course_id}", status_code=303)
    if resp.status_code != 200:
        return HTMLResponse("<h1>Курс не найден</h1>", status_code=404)
    me = await _me(request)
    return templates.TemplateResponse(
        request, "course.html", {"me": me, "course": resp.json()}
    )


@router.get("/courses/{course_id}/steps/{step_id}", response_class=HTMLResponse)
async def step(request: Request, course_id: int, step_id: int) -> Response:
    resp = await call_api(request, "GET", f"/api/v1/courses/{course_id}/steps/{step_id}")
    if resp.status_code == 401:
        return RedirectResponse(
            f"/login?next=/courses/{course_id}/steps/{step_id}", status_code=303
        )
    if resp.status_code != 200:
        return HTMLResponse("<h1>Шаг не найден</h1>", status_code=404)
    me = await _me(request)
    return templates.TemplateResponse(
        request,
        "step.html",
        {"me": me, "course_id": course_id, "step": resp.json()},
    )
