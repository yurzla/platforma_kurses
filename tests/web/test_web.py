"""Тесты web-сервиса: страницы, вход, регистрация, прокси, админ-панель."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.domain.models import ChatMessage, ChatSession, Role
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app as create_api_app
from courses_web.app import create_app as create_web_app
from courses_web.config import Settings as WebSettings
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore


def build_stack_full(store: FakeStore):
    container, _, _ = build_test_container(store)
    api_app = create_api_app(settings=container.settings, container=container)
    api_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app), base_url="http://api"
    )
    web_app = create_web_app(settings=WebSettings(api_base_url="http://api"), client=api_client)
    web_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://web"
    )
    return web_client, api_client, web_app


def build_stack(store: FakeStore):
    web_client, api_client, _ = build_stack_full(store)
    return web_client, api_client


def seed_student_and_course(store: FakeStore) -> None:
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    step = StepSummary(id=101, position=1, step_type="choice")
    lesson = LessonSummary(id=11, title="Урок 1", position=1, steps=[step])
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson])
    store.add_course(CourseDetail(id=10, title="Python", description="Основы", sections=[section]))


def seed_admin(store: FakeStore) -> None:
    store.add_user("admin@example.com", "Админ", hash_password("s3cret"), "admin")


async def test_health() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        response = await web.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_login_page_single_form() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        response = await web.get("/login")
    assert response.status_code == 200
    assert "Регистрация" in response.text
    assert 'name="email"' in response.text
    assert "Администратор" not in response.text
    assert "data-theme-toggle" in response.text
    assert "assistant-toggle" not in response.text
    assert "/static/web.css?v=" in response.text
    assert "/static/web.js?v=" not in response.text


async def test_register_page_and_flow() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        page = await web.get("/register")
        assert page.status_code == 200
        assert "Студент" in page.text
        assert "Преподаватель" in page.text

        response = await web.post(
            "/register",
            data={
                "email": "t@example.com",
                "name": "Препод",
                "password": "secret",
                "role": "teacher",
                "password_confirm": "secret",
            },
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/courses"

        me = await web.get("/api/v1/auth/me", headers={"Accept": "application/json"})
    assert me.json()["role"] == "teacher"


async def test_register_rejects_admin_role() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        response = await web.post(
            "/register",
            data={
                "email": "hack@example.com",
                "name": "Hack",
                "password": "secret",
                "role": "admin",
                "password_confirm": "secret",
            },
        )
    assert response.status_code == 422
    assert store.user_profiles == {}


async def test_register_preserves_utf8_name() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        await web.post(
            "/register",
            data={
                "email": "utf@example.com",
                "name": "Студент Ёж",
                "password": "secret",
                "role": "student",
                "password_confirm": "secret",
            },
        )
        me = await web.get("/api/v1/auth/me", headers={"Accept": "application/json"})
    assert me.json()["name"] == "Студент Ёж"


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
            data={"email": "s@example.com", "password": "pw", "next": "/courses"},
        )
        assert login.status_code == 303
        assert login.headers["location"] == "/courses"

        courses = await web.get("/courses")
        assert courses.status_code == 200
        assert "Python" in courses.text
        assert 'id="assistant-toggle"' in courses.text
        assert 'data-mode="history"' in courses.text
        assert 'id="assistant-history"' in courses.text
        assert 'id="assistant-course"' not in courses.text
        assert "/static/assistant-format.js?v=" in courses.text
        assert "/static/web.js?v=" in courses.text

        course = await web.get("/courses/10")
        assert course.status_code == 200
        assert "Урок 1" in course.text
        assert 'id="assistant-toggle"' in course.text
        assert 'data-course-id="10"' in course.text
        assert 'data-mode="course"' in course.text
        assert 'id="assistant-history"' in course.text
        assert "assistant-course-note" in course.text
        assert "Ответы по курсу" in course.text
        assert "/static/web.js?v=" in course.text

        step = await web.get("/courses/10/steps/101")
        assert step.status_code == 200
        assert "Ассистент" in step.text
        assert 'id="assistant-toggle"' in step.text
        assert 'data-mode="course"' in step.text
        assert "assistant-course-note" in step.text


async def test_course_page_shows_progress_tabs_and_structure() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses/10")
    assert page.status_code == 200
    assert "Содержание" in page.text
    assert "Описание" in page.text
    assert "Пройдено 0 из 1 шагов" in page.text
    assert "Продолжить" in page.text
    assert "data-course-tabs" in page.text
    assert "Модуль 1" in page.text
    assert "Урок 1" in page.text
    assert "/courses/10/steps/101" in page.text
    assert "/static/course.js?v=" in page.text


async def test_course_page_progress_updates_after_step_passed() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        answer = await web.post(
            "/api/v1/courses/10/steps/101/answer",
            json={"answer": None},
            headers={"Accept": "application/json"},
        )
        assert answer.status_code == 200
        page = await web.get("/courses/10")
    assert "Пройдено 1 из 1 шагов" in page.text
    assert "Курс пройден" in page.text
    assert "100%" in page.text


async def test_course_description_preserves_line_breaks() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_course(
        CourseDetail(
            id=30,
            title="Многострочный",
            description="Первый абзац\n\nВторой абзац",
        )
    )
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses/30")
    assert page.status_code == 200
    assert "Первый абзац\n\nВторой абзац" in page.text


async def test_course_card_truncates_description() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_course(
        CourseDetail(id=20, title="Длинный", description="x" * 200 + "TAIL_MARKER")
    )
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        response = await web.get("/courses")
    assert response.status_code == 200
    assert "x" * 200 + "…" in response.text
    assert "TAIL_MARKER" not in response.text


async def test_my_courses_lists_only_started() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    other_step = StepSummary(id=202, position=1, step_type="text")
    other_lesson = LessonSummary(id=12, title="Урок", position=1, steps=[other_step])
    other_section = SectionSummary(id=2, title="Модуль", position=1, lessons=[other_lesson])
    store.add_course(CourseDetail(id=11, title="OtherCourse", sections=[other_section]))
    user_id = next(iter(store.users))
    store.progress[(user_id, 101)] = "passed"
    web, api = build_stack(store)
    async with web, api:
        denied = await web.get("/my-courses")
        assert denied.status_code == 303
        assert denied.headers["location"].startswith("/login")

        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/my-courses")
    assert page.status_code == 200
    assert "Мое обучение" in page.text
    assert 'href="/my-courses"' in page.text
    assert "Python" in page.text
    assert "OtherCourse" not in page.text


async def test_my_courses_empty_state() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/my-courses")
    assert page.status_code == 200
    assert "Вы ещё не начали ни одного курса" in page.text
    assert 'href="/courses"' in page.text


async def test_bad_login_shows_error() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        response = await web.post(
            "/login", data={"email": "s@example.com", "password": "nope"}
        )
    assert response.status_code == 401
    assert "Неверный email или пароль" in response.text


async def test_courses_pagination() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    user_id = next(iter(store.users))
    for course_id in range(1, 13):
        step = StepSummary(id=course_id * 10, position=1, step_type="text")
        lesson = LessonSummary(id=course_id, title=f"Урок {course_id}", position=1, steps=[step])
        section = SectionSummary(id=course_id, title="Модуль", position=1, lessons=[lesson])
        store.add_course(CourseDetail(id=course_id, title=f"Курс {course_id}", sections=[section]))
        store.progress[(user_id, course_id * 10)] = "passed"
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})

        page1 = await web.get("/courses")
        assert page1.status_code == 200
        assert page1.text.count('class="course-card"') == 10
        assert "<h2>Курс 1</h2>" in page1.text
        assert "<h2>Курс 11</h2>" not in page1.text
        assert 'href="/courses?page=2"' in page1.text
        assert 'class="pagination"' in page1.text

        page2 = await web.get("/courses?page=2")
        assert page2.status_code == 200
        assert page2.text.count('class="course-card"') == 2
        assert "<h2>Курс 11</h2>" in page2.text
        assert "<h2>Курс 12</h2>" in page2.text

        over = await web.get("/courses?page=99", follow_redirects=False)
        assert over.status_code == 303
        assert over.headers["location"] == "/courses?page=2"

        my_page1 = await web.get("/my-courses")
        assert my_page1.status_code == 200
        assert my_page1.text.count('class="course-card"') == 10
        assert 'href="/my-courses?page=2"' in my_page1.text


async def test_assistant_history_on_course_lists() -> None:
    store = FakeStore()
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_course(CourseDetail(id=10, title="Python", sections=[]))
    store.add_course(CourseDetail(id=11, title="Django", sections=[]))
    store.sessions[1] = ChatSession(
        id=1, user_id=user.id, course_id=10, started_at=datetime.now(UTC)
    )
    store.messages[1] = [ChatMessage(session_id=1, role=Role.USER, content="вопрос по python")]
    store.sessions[2] = ChatSession(
        id=2, user_id=user.id, course_id=11, started_at=datetime.now(UTC)
    )
    store.messages[2] = [ChatMessage(session_id=2, role=Role.USER, content="вопрос по django")]
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses")
        my = await web.get("/my-courses")
        course = await web.get("/courses/10")
    assert page.status_code == 200
    assert 'data-session-id="1"' in page.text
    assert 'data-session-id="2"' in page.text
    assert "вопрос по python" in page.text
    assert "Python" in page.text
    assert "Django" in page.text
    assert "<details" in page.text
    assert my.status_code == 200
    assert 'class="history-session"' in my.text
    assert course.status_code == 200
    assert 'data-session-id="1"' in course.text
    assert 'data-session-id="2"' not in course.text


async def test_assistant_history_partial() -> None:
    store = FakeStore()
    user = store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_course(CourseDetail(id=10, title="Python", sections=[]))
    store.add_course(CourseDetail(id=11, title="Django", sections=[]))
    store.sessions[1] = ChatSession(
        id=1, user_id=user.id, course_id=10, started_at=datetime.now(UTC)
    )
    store.messages[1] = [ChatMessage(session_id=1, role=Role.USER, content="вопрос по python")]
    store.sessions[2] = ChatSession(
        id=2, user_id=user.id, course_id=11, started_at=datetime.now(UTC)
    )
    store.messages[2] = [ChatMessage(session_id=2, role=Role.USER, content="вопрос по django")]
    web, api = build_stack(store)
    async with web, api:
        anon = await web.get("/assistant/history")
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        all_resp = await web.get("/assistant/history")
        scoped = await web.get("/assistant/history?course_id=10")
    assert anon.status_code == 401
    assert all_resp.status_code == 200
    assert 'data-session-id="1"' in all_resp.text
    assert 'data-session-id="2"' in all_resp.text
    assert "<details" in all_resp.text
    assert scoped.status_code == 200
    assert 'data-session-id="1"' in scoped.text
    assert 'data-session-id="2"' not in scoped.text



async def test_courses_single_page_has_no_pagination() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        response = await web.get("/courses")
    assert response.status_code == 200
    assert 'class="pagination"' not in response.text


async def test_proxy_forwards_auth_me() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post(
            "/login", data={"email": "s@example.com", "password": "pw"}
        )
        response = await web.get("/api/v1/auth/me", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["role"] == "student"


async def test_sessions_not_shared_between_browsers() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api, web_app = build_stack_full(store)
    other = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=web_app), base_url="http://web"
    )
    async with web, api, other:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        mine = await web.get("/api/v1/auth/me", headers={"Accept": "application/json"})
        anon = await other.get("/api/v1/auth/me", headers={"Accept": "application/json"})
    assert mine.json()["role"] == "student"
    assert anon.json()["role"] is None


async def test_admin_panel_flow() -> None:
    store = FakeStore()
    seed_admin(store)
    web, api = build_stack(store)
    async with web, api:
        redirect = await web.get("/dashboard")
        assert redirect.status_code == 303
        assert "next=/dashboard" in redirect.headers["location"]

        await web.post(
            "/login", data={"email": "admin@example.com", "password": "s3cret"}
        )
        dashboard = await web.get("/dashboard")
        assert dashboard.status_code == 200
        assert "Админ панель" in dashboard.text
        assert "Пользователи" in dashboard.text
        assert "/static/dashboard.js" in dashboard.text
        assert 'id="assistant-toggle"' not in dashboard.text


async def test_static_assets_served() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        assert (await web.get("/static/theme.js")).status_code == 200
        assert (await web.get("/static/dashboard.css")).status_code == 200
        assert (await web.get("/static/web.js")).status_code == 200
        css = await web.get("/static/web.css")
    assert css.status_code == 200
    assert "right: 20px; bottom: 20px" in css.text
    assert "repeat(2, minmax(0, 1fr))" in css.text
    assert ".pagination" in css.text


async def test_proxy_auto_refreshes_expired_access_token() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        for cookie in web.cookies.jar:
            if cookie.name == "access_token":
                cookie.value = "broken-token"

        response = await web.get("/api/v1/courses", headers={"Accept": "application/json"})
        assert response.status_code == 200
        assert response.json()
        assert all(cookie.value != "broken-token" for cookie in web.cookies.jar)
