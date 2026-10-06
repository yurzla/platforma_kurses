"""HTML-страницы web-сервиса (Jinja2 поверх JSON API)."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from courses_web.client import call_api, relay_cookies, relay_refreshed
from courses_web.templating import templates

router = APIRouter(tags=["pages"])

_REGISTER_ROLES = ("student", "teacher")


def _render(
    request: Request,
    name: str,
    context: dict[str, Any],
    status_code: int = 200,
) -> Response:
    response = templates.TemplateResponse(request, name, context, status_code=status_code)
    relay_refreshed(response, request)
    return response


async def _form(request: Request) -> dict[str, str]:
    """Разбор urlencoded-формы как UTF-8 (request.form() декодирует как latin-1)."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/x-www-form-urlencoded"):
        body = await request.body()
        return dict(parse_qsl(body.decode("utf-8"), keep_blank_values=True))
    form = await request.form()
    return {key: str(value) for key, value in form.items()}


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
async def login_page(request: Request, next: str = "") -> Response:
    return templates.TemplateResponse(
        request, "login.html", {"next": next, "me": {"role": None}}
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request) -> Response:
    form = await _form(request)
    next_raw = form.get("next")
    upstream = await call_api(
        request,
        "POST",
        "/api/v1/auth/login",
        json={"email": form.get("email", ""), "password": form.get("password", "")},
    )
    if upstream.status_code == 200:
        role = upstream.json().get("role")
        fallback = "/dashboard" if role == "admin" else "/courses"
        response = RedirectResponse(_safe_next(next_raw, fallback), status_code=303)
        relay_cookies(response, upstream)
        return response

    context = {
        "next": next_raw or "",
        "error": "Неверный email или пароль",
        "email": form.get("email", ""),
        "me": {"role": None},
    }
    return templates.TemplateResponse(request, "login.html", context, status_code=401)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request, "register.html", {"roles": _REGISTER_ROLES, "me": {"role": None}}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_submit(request: Request) -> Response:
    form = await _form(request)
    role = form.get("role", "student")
    context = {
        "roles": _REGISTER_ROLES,
        "email": form.get("email", ""),
        "name": form.get("name", ""),
        "role": role,
        "me": {"role": None},
    }
    if role not in _REGISTER_ROLES:
        context["error"] = "Роль недоступна при регистрации"
        return templates.TemplateResponse(request, "register.html", context, status_code=422)

    upstream = await call_api(
        request,
        "POST",
        "/api/v1/auth/register",
        json={
            "email": form.get("email", ""),
            "name": form.get("name", ""),
            "password": form.get("password", ""),
            "role": role,
        },
    )
    if upstream.status_code == 201:
        response = RedirectResponse("/courses", status_code=303)
        relay_cookies(response, upstream)
        return response

    if upstream.status_code == 409:
        context["error"] = "Пользователь с таким email уже зарегистрирован"
    elif upstream.status_code == 422:
        context["error"] = "Проверьте правильность заполнения полей"
    else:
        context["error"] = "Не удалось зарегистрироваться"
    return templates.TemplateResponse(
        request, "register.html", context, status_code=upstream.status_code
    )


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    upstream = await call_api(request, "POST", "/api/v1/auth/logout")
    response = RedirectResponse("/login", status_code=303)
    relay_cookies(response, upstream)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    me = await _me(request)
    if me.get("role") != "admin":
        return RedirectResponse("/login?next=/dashboard", status_code=303)
    return _render(request, "dashboard.html", {"me": me})


@router.get("/courses", response_class=HTMLResponse)
async def courses(request: Request) -> Response:
    resp = await call_api(request, "GET", "/api/v1/courses")
    if resp.status_code == 401:
        return RedirectResponse("/login?next=/courses", status_code=303)
    me = await _me(request)
    return _render(
        request,
        "courses.html",
        {"me": me, "courses": resp.json() if resp.status_code == 200 else []},
    )


@router.get("/my-courses", response_class=HTMLResponse)
async def my_courses(request: Request) -> Response:
    resp = await call_api(request, "GET", "/api/v1/courses", params=[("enrolled", "true")])
    if resp.status_code == 401:
        return RedirectResponse("/login?next=/my-courses", status_code=303)
    me = await _me(request)
    return _render(
        request,
        "my_courses.html",
        {"me": me, "courses": resp.json() if resp.status_code == 200 else []},
    )


def _course_progress(course_id: int, course: dict[str, Any]) -> dict[str, Any]:
    total = 0
    done = 0
    next_href: str | None = None
    for section in course.get("sections", []):
        for lesson in section.get("lessons", []):
            for step in lesson.get("steps", []):
                total += 1
                if step.get("completed"):
                    done += 1
                elif next_href is None:
                    next_href = f"/courses/{course_id}/steps/{step.get('id')}"
    percent = round(100.0 * done / total, 1) if total else 0.0
    return {
        "percent": percent,
        "done": done,
        "total": total,
        "next_href": next_href,
        "completed": total > 0 and done >= total,
    }


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course(request: Request, course_id: int) -> Response:
    resp = await call_api(request, "GET", f"/api/v1/courses/{course_id}")
    if resp.status_code == 401:
        return RedirectResponse(f"/login?next=/courses/{course_id}", status_code=303)
    if resp.status_code != 200:
        return HTMLResponse("<h1>Курс не найден</h1>", status_code=404)
    me = await _me(request)
    course_data = resp.json()
    return _render(
        request,
        "course.html",
        {
            "me": me,
            "course": course_data,
            "course_id": course_id,
            "progress": _course_progress(course_id, course_data),
        },
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
    return _render(
        request,
        "step.html",
        {"me": me, "course_id": course_id, "step": resp.json()},
    )
