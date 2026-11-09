"""HTML-страницы web-сервиса (Jinja2 поверх JSON API)."""

from __future__ import annotations

from datetime import datetime
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


async def _require_teacher_page(request: Request) -> dict[str, Any] | RedirectResponse:
    me = await _me(request)
    if me.get("role") == "teacher":
        return me
    return RedirectResponse("/login?next=/teacher", status_code=303)


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


_COURSES_PAGE_SIZE = 10


def _course_list_params(enrolled: bool, page: int) -> list[tuple[str, str]]:
    params = [
        ("limit", str(_COURSES_PAGE_SIZE)),
        ("offset", str((page - 1) * _COURSES_PAGE_SIZE)),
    ]
    if enrolled:
        params.append(("enrolled", "true"))
    return params


def _course_list_context(data: dict[str, Any], *, page: int, path: str) -> dict[str, Any]:
    limit = int(data.get("limit", _COURSES_PAGE_SIZE)) or _COURSES_PAGE_SIZE
    total = int(data.get("total", 0))
    pages = (total + limit - 1) // limit if total else 0
    return {
        "courses": data.get("items", []),
        "page": page,
        "pages": pages,
        "total": total,
        "base_path": path,
    }


async def _courses_page(
    request: Request, *, path: str, template: str, enrolled: bool, page: int
) -> Response:
    page = max(page, 1)
    resp = await call_api(
        request, "GET", "/api/v1/courses", params=_course_list_params(enrolled, page)
    )
    if resp.status_code == 401:
        return RedirectResponse(f"/login?next={path}", status_code=303)
    data = resp.json() if resp.status_code == 200 else {}
    context = _course_list_context(data, page=page, path=path)
    if context["pages"] and page > context["pages"]:
        return RedirectResponse(f"{path}?page={context['pages']}", status_code=303)
    me = await _me(request)
    assistant = await _assistant_history_context(request)
    return _render(
        request,
        template,
        {"me": me, "assistant_mode": "history", **context, **assistant},
    )


def _format_started_at(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value


async def _assistant_history_context(
    request: Request, *, course_id: int | None = None
) -> dict[str, Any]:
    sessions_resp = await call_api(request, "GET", "/api/v1/chat/sessions")
    sessions = sessions_resp.json() if sessions_resp.status_code == 200 else []

    groups: dict[Any, dict[str, Any]] = {}
    for session in sessions:
        if course_id is not None and session.get("course_id") != course_id:
            continue
        group = groups.setdefault(
            session.get("course_id"),
            {"title": session.get("course_title") or "Все курсы", "sessions": []},
        )
        group["sessions"].append(
            {
                "id": session.get("id"),
                "started_at": _format_started_at(session.get("started_at")),
                "preview": (session.get("last_message") or "").strip()[:140],
            }
        )
    return {"assistant_history": list(groups.values())}


@router.get("/assistant/history", response_class=HTMLResponse)
async def assistant_history(request: Request, course_id: int | None = None) -> Response:
    me = await _me(request)
    if not me.get("role"):
        return HTMLResponse("", status_code=401)
    context = await _assistant_history_context(request, course_id=course_id)
    return _render(request, "_assistant_history.html", context)


@router.get("/courses", response_class=HTMLResponse)
async def courses(request: Request, page: int = 1) -> Response:
    return await _courses_page(
        request, path="/courses", template="courses.html", enrolled=False, page=page
    )


@router.get("/my-courses", response_class=HTMLResponse)
async def my_courses(request: Request, page: int = 1) -> Response:
    return await _courses_page(
        request, path="/my-courses", template="my_courses.html", enrolled=True, page=page
    )


@router.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(request: Request) -> Response:
    me = await _require_teacher_page(request)
    if isinstance(me, RedirectResponse):
        return me
    response = await call_api(request, "GET", "/api/v1/teacher/courses")
    courses = response.json() if response.status_code == 200 else []
    return _render(request, "teacher_dashboard.html", {"me": me, "courses": courses})


@router.post("/teacher/courses")
async def teacher_create_course(request: Request) -> Response:
    me = await _require_teacher_page(request)
    if isinstance(me, RedirectResponse):
        return me
    form = await _form(request)
    response = await call_api(
        request, "POST", "/api/v1/teacher/courses",
        json={"title": form.get("title", ""), "description": form.get("description") or None, "level": form.get("level") or None},
    )
    if response.status_code == 201:
        return RedirectResponse(f"/teacher/courses/{response.json()['id']}", status_code=303)
    courses_response = await call_api(request, "GET", "/api/v1/teacher/courses")
    return _render(request, "teacher_dashboard.html", {
        "me": me, "courses": courses_response.json() if courses_response.status_code == 200 else [],
        "error": response.json().get("detail", "Не удалось создать курс"),
    }, status_code=response.status_code)


@router.get("/teacher/courses/{course_id}", response_class=HTMLResponse)
async def teacher_course(request: Request, course_id: int) -> Response:
    me = await _require_teacher_page(request)
    if isinstance(me, RedirectResponse):
        return me
    course_response = await call_api(request, "GET", f"/api/v1/teacher/courses/{course_id}")
    if course_response.status_code != 200:
        return HTMLResponse("<h1>Курс не найден или недоступен</h1>", status_code=course_response.status_code)
    students_response = await call_api(request, "GET", f"/api/v1/teacher/courses/{course_id}/students")
    return _render(request, "teacher_course.html", {
        "me": me,
        "course": course_response.json(),
        "students": students_response.json() if students_response.status_code == 200 else [],
    })


@router.post("/teacher/courses/{course_id}/settings")
async def teacher_update_course(request: Request, course_id: int) -> Response:
    form = await _form(request)
    payload = {
        "title": form.get("title", ""),
        "description": form.get("description") or None,
        "level": form.get("level") or None,
        "is_published": form.get("is_published") == "on",
    }
    response = await call_api(request, "PATCH", f"/api/v1/teacher/courses/{course_id}", json=payload)
    if response.status_code == 200:
        return RedirectResponse("/teacher", status_code=303)
    return RedirectResponse(f"/teacher/courses/{course_id}?error=save", status_code=303)


@router.post("/teacher/courses/{course_id}/sections")
async def teacher_create_section(request: Request, course_id: int) -> Response:
    form = await _form(request)
    await call_api(request, "POST", f"/api/v1/teacher/courses/{course_id}/sections", json={"title": form.get("title", "")})
    return RedirectResponse(f"/teacher/courses/{course_id}", status_code=303)


@router.post("/teacher/sections/{section_id}/lessons")
async def teacher_create_lesson(request: Request, section_id: int) -> Response:
    form = await _form(request)
    course_id = form.get("course_id", "")
    await call_api(request, "POST", f"/api/v1/teacher/sections/{section_id}/lessons", json={"title": form.get("title", "")})
    return RedirectResponse(f"/teacher/courses/{course_id}", status_code=303)


@router.post("/teacher/sections/{section_id}/delete")
async def teacher_delete_section(request: Request, section_id: int) -> Response:
    form = await _form(request)
    course_id = form.get("course_id", "")
    await call_api(request, "DELETE", f"/api/v1/teacher/sections/{section_id}")
    return RedirectResponse(f"/teacher/courses/{course_id}", status_code=303)


@router.post("/teacher/lessons/{lesson_id}/delete")
async def teacher_delete_lesson(request: Request, lesson_id: int) -> Response:
    form = await _form(request)
    course_id = form.get("course_id", "")
    await call_api(request, "DELETE", f"/api/v1/teacher/lessons/{lesson_id}")
    return RedirectResponse(f"/teacher/courses/{course_id}", status_code=303)


@router.post("/teacher/lessons/{lesson_id}/steps")
async def teacher_create_step(request: Request, lesson_id: int) -> Response:
    form = await _form(request)
    course_id = form.get("course_id", "")
    step_type = form.get("step_type", "text")
    choices = [
        {"text": form.get(f"choice_{index}", ""), "is_correct": form.get(f"correct_{index}") == "on"}
        for index in range(1, 5)
        if form.get(f"choice_{index}", "").strip()
    ]
    response = await call_api(request, "POST", f"/api/v1/teacher/lessons/{lesson_id}/steps", json={
        "body": form.get("body", ""), "step_type": step_type, "choices": choices,
        "is_multiple_choice": form.get("is_multiple_choice") == "on",
        "correct_answer": form.get("correct_answer") or None,
    })
    if response.status_code != 201:
        return RedirectResponse(f"/teacher/courses/{course_id}?error=step", status_code=303)
    return RedirectResponse(f"/teacher/courses/{course_id}", status_code=303)


@router.post("/teacher/courses/{course_id}/delete")
async def teacher_delete_draft(request: Request, course_id: int) -> Response:
    await call_api(request, "DELETE", f"/api/v1/teacher/courses/{course_id}")
    return RedirectResponse("/teacher", status_code=303)


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


def _step_neighbours(
    course_data: dict[str, Any], step_id: int
) -> tuple[int | None, int | None]:
    step_ids = [
        step.get("id")
        for section in course_data.get("sections", [])
        for lesson in section.get("lessons", [])
        for step in lesson.get("steps", [])
    ]
    try:
        index = step_ids.index(step_id)
    except ValueError:
        return None, None
    previous_id = step_ids[index - 1] if index > 0 else None
    next_id = step_ids[index + 1] if index + 1 < len(step_ids) else None
    return previous_id, next_id


def _step_markers(course: dict[str, Any], done: int) -> list[dict[str, Any]]:
    sections = course.get("sections", [])
    total = sum(
        1
        for section in sections
        for lesson in section.get("lessons", [])
        for _step in lesson.get("steps", [])
    )
    if total == 0:
        return []
    markers: list[dict[str, Any]] = []
    cumulative = 0
    for index, section in enumerate(sections, start=1):
        lessons = section.get("lessons", [])
        section_size = sum(len(lesson.get("steps", [])) for lesson in lessons)
        if section_size == 0:
            continue
        section_end = cumulative + section_size
        module_title = section.get("title") or f"Модуль {index}"
        for lesson in lessons:
            steps = lesson.get("steps", [])
            if not steps:
                continue
            cumulative += len(steps)
            if cumulative >= total:
                continue
            if cumulative == section_end:
                markers.append(
                    {
                        "percent": round(100.0 * cumulative / total, 2),
                        "kind": "module",
                        "title": module_title,
                        "step": cumulative,
                        "reached": cumulative <= done,
                    }
                )
            else:
                markers.append(
                    {
                        "percent": round(100.0 * cumulative / total, 2),
                        "kind": "lesson",
                        "title": lesson.get("title") or f"Этап {index}",
                        "step": cumulative,
                        "reached": cumulative <= done,
                    }
                )
    return markers


def _step_context(course: dict[str, Any], step_id: int) -> dict[str, Any]:
    context: dict[str, Any] = {
        "course_title": course.get("title"),
        "section_title": None,
        "lesson_title": None,
        "number": None,
    }
    number = 0
    for section in course.get("sections", []):
        for lesson in section.get("lessons", []):
            for step in lesson.get("steps", []):
                number += 1
                if step.get("id") == step_id:
                    context["section_title"] = section.get("title")
                    context["lesson_title"] = lesson.get("title")
                    context["number"] = number
                    return context
    return context


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course(request: Request, course_id: int) -> Response:
    resp = await call_api(request, "GET", f"/api/v1/courses/{course_id}")
    if resp.status_code == 401:
        return RedirectResponse(f"/login?next=/courses/{course_id}", status_code=303)
    if resp.status_code != 200:
        return HTMLResponse("<h1>Курс не найден</h1>", status_code=404)
    me = await _me(request)
    course_data = resp.json()
    assistant = await _assistant_history_context(request, course_id=course_id)
    return _render(
        request,
        "course.html",
        {
            "me": me,
            "course": course_data,
            "course_id": course_id,
            "assistant_mode": "course",
            "assistant_course_title": course_data.get("title"),
            "progress": _course_progress(course_id, course_data),
            **assistant,
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
    step_data = resp.json()
    course_resp = await call_api(request, "GET", f"/api/v1/courses/{course_id}")
    course_data = course_resp.json() if course_resp.status_code == 200 else {}
    course_title = course_data.get("title")
    previous_step_id, next_step_id = _step_neighbours(course_data, step_id)
    progress = _course_progress(course_id, course_data)
    assistant = await _assistant_history_context(request, course_id=course_id)
    return _render(
        request,
        "step.html",
        {
            "me": me,
            "course_id": course_id,
            "assistant_mode": "course",
            "assistant_course_title": course_title,
            "step": step_data,
            "prev_step_id": previous_step_id,
            "next_step_id": next_step_id,
            "progress": progress,
            "checkpoints": _step_markers(course_data, progress["done"]),
            "step_context": _step_context(course_data, step_id),
            "step_progress": {"done": progress["done"], "total": progress["total"]},
            **assistant,
        },
    )
