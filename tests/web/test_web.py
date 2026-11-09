"""Тесты web-сервиса: страницы, вход, регистрация, прокси, админ-панель."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
from fastapi.routing import APIRoute

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.domain.models import ChatMessage, ChatSession, Role
from courses_assistant.entrypoints.api.app import create_app as create_api_app
from courses_web.app import create_app as create_web_app
from courses_web.config import Settings as WebSettings
from courses_web.routers import pages
from courses_web.templating import templates
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore, encrypt_test_password


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
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    step = StepSummary(id=101, position=1, step_type="choice")
    lesson = LessonSummary(id=11, title="Урок 1", position=1, steps=[step])
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson])
    store.add_course(CourseDetail(id=10, title="Python", description="Основы", sections=[section]))


def seed_admin(store: FakeStore) -> None:
    store.add_user("admin@example.com", "Админ", encrypt_test_password("s3cret"), "admin")


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
        assert 'aria-label="Ассистент"' in courses.text
        assert "bi bi-robot" in courses.text
        assert "bi bi-search" in courses.text
        assert ">Найти<" not in courses.text
        assert "· обучение" not in courses.text
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
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
    user = store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
    user = store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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
        assert "Индекс" in dashboard.text
        assert "Состояние" in dashboard.text
        assert 'id="job-modal"' in dashboard.text
        assert 'id="chunk-modal"' in dashboard.text
        assert 'class="index-stack"' in dashboard.text
        assert 'id="index-courses-without-embeddings"' in dashboard.text
        assert 'id="index-courses-without-chunks"' in dashboard.text
        assert 'data-diagnostic="chunks"' in dashboard.text
        assert 'id="diagnostic-chunks"' in dashboard.text
        assert 'id="chunks-body"' in dashboard.text
        index_panel = dashboard.text.split('id="diagnostic-index"', 1)[1].split(
            'id="diagnostic-chunks"', 1
        )[0]
        assert 'id="chunks-body"' not in index_panel
        assert 'class="f-course"' in dashboard.text
        assert 'class="f-status"' in dashboard.text
        assert "/static/dashboard.js" in dashboard.text
        assert 'id="assistant-toggle"' not in dashboard.text
        lowered = dashboard.text.lower()
        assert "retry" not in lowered
        assert "replay" not in lowered


async def test_static_assets_served() -> None:
    store = FakeStore()
    web, api = build_stack(store)
    async with web, api:
        assert (await web.get("/static/theme.js")).status_code == 200
        assert (await web.get("/static/dashboard.css")).status_code == 200
        assert (await web.get("/static/web.js")).status_code == 200
        css = await web.get("/static/web.css")
        dashboard = await web.get("/static/dashboard.css")
        js = await web.get("/static/dashboard.js")
        icons = await web.get("/static/vendor/bootstrap-icons/bootstrap-icons.min.css")
        font = await web.get("/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2")
    assert css.status_code == 200
    assert "right: 20px; bottom: 20px" in css.text
    assert "repeat(2, minmax(0, 1fr))" in css.text
    assert ".pagination" in css.text
    assert ".step-form .choice-editor" in css.text
    assert "grid-template-columns: auto 1fr" in css.text
    assert dashboard.status_code == 200
    assert "text-decoration: none" in dashboard.text
    assert ".modal-backdrop" in dashboard.text
    assert ".filters input, .filters select, .filters .btn" in dashboard.text
    assert "height: 38px" in dashboard.text
    assert "#jobs-filters, #chunks-filters { flex-wrap: nowrap; }" in dashboard.text
    assert "#f-apply, #ch-apply { margin-left: auto; }" in dashboard.text
    assert "text-overflow: ellipsis" in dashboard.text
    assert js.status_code == 200
    assert "openJob(" in js.text
    assert "loadIndex(" in js.text
    assert "loadChunksTab(" in js.text
    assert "const courseSignature" in js.text
    assert "dataset.signature" in js.text
    assert "loadHealth(" in js.text
    assert "course_recommendation" in js.text
    assert "Рекомендованные курсы" in js.text
    assert "нет чанков" in js.text
    assert "нет эмбеддингов" in js.text
    assert "retry" not in js.text.lower()
    assert "replay" not in js.text.lower()
    assert icons.status_code == 200
    assert "bootstrap-icons" in icons.text
    assert font.status_code == 200


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


def _search_course(course_id: int, title: str, description: str | None, step_id: int):
    step = StepSummary(id=step_id, position=1, step_type="text")
    lesson = LessonSummary(id=course_id, title="Урок", position=1, steps=[step])
    section = SectionSummary(id=course_id, title="Модуль", position=1, lessons=[lesson])
    return CourseDetail(id=course_id, title=title, description=description, sections=[section])


async def test_courses_search_filters_and_reset() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(_search_course(1, "Python", "Основы", 101))
    store.add_course(_search_course(2, "Django", "Веб на Python", 201))
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})

        found = await web.get("/courses?search=django")
        assert found.status_code == 200
        assert "Django" in found.text
        assert "<h2>Python</h2>" not in found.text
        assert 'name="search" value="django"' in found.text
        assert 'href="/courses">Сбросить' in found.text

        by_description = await web.get("/courses?search=python")
        assert by_description.text.count('class="course-card"') == 2

        empty = await web.get("/courses?search=%D0%BD%D0%B5%D1%82")
        assert empty.status_code == 200
        assert "ничего не найдено" in empty.text
        assert "Доступных курсов нет" not in empty.text


async def test_my_courses_search_keeps_enrollment_filter() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    user_id = next(iter(store.users))
    store.add_course(_search_course(1, "Python", None, 101))
    store.add_course(_search_course(2, "Python Advanced", None, 201))
    store.progress[(user_id, 101)] = "passed"
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/my-courses?search=python")
    assert page.status_code == 200
    assert "<h2>Python</h2>" in page.text
    assert "<h2>Python Advanced</h2>" not in page.text
    assert 'name="search" value="python"' in page.text


async def test_courses_pagination_preserves_search() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    for course_id in range(1, 12):
        store.add_course(_search_course(course_id, f"Python {course_id}", None, course_id * 10))
    store.add_course(_search_course(99, "Django", None, 990))
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})

        page1 = await web.get("/courses?search=python")
        assert page1.status_code == 200
        assert page1.text.count('class="course-card"') == 10
        assert 'href="/courses?page=2&amp;search=python"' in page1.text

        page2 = await web.get("/courses?page=2&search=python")
        assert page2.text.count('class="course-card"') == 1
        assert "Django" not in page2.text

        over = await web.get("/courses?page=99&search=python", follow_redirects=False)
        assert over.status_code == 303
        assert over.headers["location"] == "/courses?page=2&search=python"


def _seed_teacher_courses(store: FakeStore, count: int):
    teacher = store.add_user(
        "t@example.com", "Учитель", encrypt_test_password("pw"), "teacher"
    )
    for course_id in range(1, count + 1):
        store.add_course(
            _search_course(course_id, f"Курс {course_id}", None, course_id * 10),
            owner_id=teacher.id,
        )
    return teacher


async def test_teacher_page_pagination_and_search() -> None:
    store = FakeStore()
    _seed_teacher_courses(store, 12)
    store.add_course(_search_course(99, "Django", None, 990), owner_id=1)
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "t@example.com", "password": "pw"})

        page1 = await web.get("/teacher")
        assert page1.status_code == 200
        assert page1.text.count('class="teacher-course-card"') == 10
        assert 'href="/teacher?page=2"' in page1.text

        page2 = await web.get("/teacher?page=2")
        assert page2.text.count('class="teacher-course-card"') == 3

        found = await web.get("/teacher?search=django")
        assert found.text.count('class="teacher-course-card"') == 1
        assert "Django" in found.text
        assert 'name="search" value="django"' in found.text

        empty = await web.get("/teacher?search=%D0%BD%D0%B5%D1%82")
        assert "ничего не найдено" in empty.text
        assert 'href="/teacher">Сбросить' in empty.text

        over = await web.get("/teacher?page=99", follow_redirects=False)
        assert over.status_code == 303
        assert over.headers["location"] == "/teacher?page=2"


async def test_step_page_renders_video_player() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    store.step_video_urls[101] = "https://youtu.be/abc123"
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses/10/steps/101")
        assert page.status_code == 200
        assert 'class="step-video"' in page.text
        assert 'src="https://www.youtube.com/embed/abc123"' in page.text

        store.step_video_urls[101] = "https://cdn.example.com/lesson.mp4"
        page = await web.get("/courses/10/steps/101")
        assert "<video controls" in page.text
        assert 'src="https://cdn.example.com/lesson.mp4"' in page.text


def test_teacher_course_step_forms_render() -> None:
    course = {
        "id": 5,
        "title": "Курс",
        "description": None,
        "level": None,
        "is_published": False,
        "sections": [
            {
                "id": 1,
                "title": "Модуль",
                "position": 1,
                "lessons": [
                    {
                        "id": 2,
                        "title": "Урок",
                        "position": 1,
                        "steps": [
                            {
                                "id": 101,
                                "position": 1,
                                "step_type": "choice",
                                "body": "Вопрос",
                                "video_url": "https://youtu.be/abc123",
                                "choices": [
                                    {"text": "A", "is_correct": True},
                                    {"text": "B", "is_correct": False},
                                ],
                                "is_multiple_choice": False,
                                "correct_answer": None,
                            }
                        ],
                    }
                ],
            }
        ],
    }
    html = templates.env.get_template("teacher_course.html").render(
        request=SimpleNamespace(query_params={}),
        me={"role": "teacher", "name": "Учитель"},
        course=course,
        students=[],
    )
    assert "Шаг 1 · Тест" in html
    assert 'action="/teacher/steps/101"' in html
    assert 'action="/teacher/steps/101/delete"' in html
    assert 'action="/teacher/lessons/2/steps"' in html
    assert 'name="video_url"' in html
    assert 'value="https://youtu.be/abc123"' in html
    assert 'name="course_id" value="5"' in html
    assert "Подсказка по форматированию" in html
    assert "Markdown" in html
    assert ">Вопрос</textarea>" in html
    assert 'value="A"' in html
    assert 'class="choice-editor"' in html
    assert 'name="correct_1"' in html
    assert 'name="choice_1"' in html
    assert "Добавить шаг" in html


def test_step_create_form_route_has_single_handler() -> None:
    handlers = [
        route.endpoint.__name__
        for route in pages.router.routes
        if isinstance(route, APIRoute)
        and route.path == "/teacher/lessons/{lesson_id}/steps"
        and "POST" in route.methods
    ]
    assert handlers == ["teacher_create_step"]


async def test_step_page_renders_markdown_body() -> None:
    store = FakeStore()
    seed_student_and_course(store)
    store.step_bodies[101] = "**Жирный** текст\nвторая строка"
    web, api = build_stack(store)
    async with web, api:
        await web.post("/login", data={"email": "s@example.com", "password": "pw"})
        page = await web.get("/courses/10/steps/101")
        assert page.status_code == 200
        assert "<strong>Жирный</strong>" in page.text
        assert "<br" in page.text
        assert "**Жирный**" not in page.text

        store.step_bodies[101] = '<p>Старый</p><iframe src="https://youtu.be/x"></iframe>'
        legacy = await web.get("/courses/10/steps/101")
        assert "<p>Старый</p>" in legacy.text
        assert '<iframe src="https://youtu.be/x"></iframe>' in legacy.text
