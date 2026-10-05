"""Тесты web-сервиса: страницы, вход, прокси, дашборд."""

from __future__ import annotations

import httpx

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app as create_api_app
from courses_web.app import create_app as create_web_app
from courses_web.config import Settings as WebSettings
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def build_stack(store: FakeStore, *, admin: bool = False):
    container, _, _ = build_test_container(store)
    if admin:
        container.settings.admin_username = "admin"
        container.settings.admin_password = "s3cret"
    api_app = create_api_app(settings=container.settings, container=container)
    api_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app), base_url="http://api"
    )
    web_app = create_web_app(settings=WebSettings(api_base_url="http://api"), client=api_client)
    web_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://web"
    )
    return web_client, api_client


def seed_student_and_course(store: FakeStore) -> None:
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    step = StepSummary(id=101, position=1, step_type="choice")
    lesson = LessonSummary(id=11, title="Урок 1", position=1, steps=[step])
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson])
    store.add_course(CourseDetail(id=10, title="Python", description="Основы", sections=[section]))


async def test_health() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        response = await web.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_login_page_has_role_switch() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        response = await web.get("/login")
    assert response.status_code == 200
    assert "Студент" in response.text
    assert "Администратор" in response.text
    assert "data-theme-toggle" in response.text


async def test_student_login_flow_and_courses() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        denied = await web.get("/courses")
        assert denied.status_code == 303
        assert denied.headers["location"].startswith("/login")

        login = await web.post(
            "/login",
            data={
                "role": "student",
                "email": "s@example.com",
                "password": "pw",
                "next": "/courses",
            },
        )
        assert login.status_code == 303
        assert login.headers["location"] == "/courses"

        courses = await web.get("/courses")
        assert courses.status_code == 200
        assert "Python" in courses.text

        course = await web.get("/courses/10")
        assert course.status_code == 200
        assert "Урок 1" in course.text

        step = await web.get("/courses/10/steps/101")
        assert step.status_code == 200
        assert "Ассистент" in step.text


async def test_bad_login_shows_error() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        response = await web.post(
            "/login",
            data={"role": "student", "email": "s@example.com", "password": "nope"},
        )
    assert response.status_code == 401
    assert "Неверный логин или пароль" in response.text


async def test_proxy_forwards_auth_me() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post(
            "/login",
            data={"role": "student", "email": "s@example.com", "password": "pw"},
        )
        response = await web.get("/api/v1/auth/me", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["role"] == "student"


async def test_admin_dashboard_flow() -> None:
    store = FakeStore()
    web, api = build_stack(store, admin=True)
    async with web, api:
        redirect = await web.get("/dashboard")
        assert redirect.status_code == 303
        assert "role=admin" in redirect.headers["location"]

        await web.post(
            "/login",
            data={"role": "admin", "username": "admin", "password": "s3cret"},
        )
        dashboard = await web.get("/dashboard")
        assert dashboard.status_code == 200
        assert "Jobs" in dashboard.text
        assert "/static/dashboard.js" in dashboard.text


async def test_static_assets_served() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        assert (await web.get("/static/theme.js")).status_code == 200
        assert (await web.get("/static/dashboard.css")).status_code == 200
        assert (await web.get("/static/web.js")).status_code == 200
