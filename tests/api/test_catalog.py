"""API-тесты каталога: курсы, шаги, ответы, прогресс."""

from __future__ import annotations

import httpx

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.domain.security import hash_password
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore

CHOICE_KEY = {
    "name": "choice",
    "options": {"is_multiple_choice": False},
    "choices": [
        {"id": 1, "text": "A", "is_correct": True},
        {"id": 2, "text": "B", "is_correct": False},
    ],
}


def build_course() -> CourseDetail:
    step = StepSummary(id=101, position=1, step_type="choice")
    lesson = LessonSummary(id=11, title="Урок 1", position=1, steps=[step])
    section = SectionSummary(id=1, title="Модуль 1", position=1, lessons=[lesson])
    return CourseDetail(id=10, title="Python", description="Основы", sections=[section])


def make_app(store: FakeStore):
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def _login(ac: httpx.AsyncClient) -> None:
    await ac.post(
        "/api/v1/auth/student/login", json={"email": "s@example.com", "password": "pw"}
    )


async def test_catalog_requires_login() -> None:
    store = FakeStore()
    store.add_course(build_course())
    ac = make_app(store)
    async with ac:
        assert (await ac.get("/api/v1/courses")).status_code == 401


async def test_course_and_step_flow() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    store.add_course(build_course())
    store.answer_keys[101] = CHOICE_KEY
    ac = make_app(store)
    async with ac:
        await _login(ac)

        courses = await ac.get("/api/v1/courses")
        assert courses.status_code == 200
        assert courses.json()[0]["id"] == 10
        assert courses.json()[0]["steps_count"] == 1

        course = await ac.get("/api/v1/courses/10")
        assert course.status_code == 200
        assert course.json()["sections"][0]["lessons"][0]["steps"][0]["id"] == 101

        step = await ac.get("/api/v1/courses/10/steps/101")
        assert step.status_code == 200
        body = step.json()
        assert body["grading"] == "auto"
        assert body["options"]["choices"][0]["id"] == 1
        assert "is_correct" not in body["options"]["choices"][0]

        wrong = await ac.post("/api/v1/courses/10/steps/101/answer", json={"answer": [2]})
        assert wrong.status_code == 200
        assert wrong.json()["is_correct"] is False

        right = await ac.post("/api/v1/courses/10/steps/101/answer", json={"answer": [1]})
        assert right.json()["is_correct"] is True
        assert right.json()["progress_percent"] == 100.0

        course_after = await ac.get("/api/v1/courses/10")
        assert course_after.json()["sections"][0]["lessons"][0]["steps"][0]["completed"] is True


async def test_manual_step_completion() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", hash_password("pw"), "student")
    step = StepSummary(id=202, position=1, step_type="code")
    lesson = LessonSummary(id=12, title="Урок", position=1, steps=[step])
    section = SectionSummary(id=2, title="Модуль", position=1, lessons=[lesson])
    store.add_course(CourseDetail(id=11, title="Code", sections=[section]))
    ac = make_app(store)
    async with ac:
        await _login(ac)
        detail = await ac.get("/api/v1/courses/11/steps/202")
        assert detail.json()["grading"] == "manual"

        result = await ac.post("/api/v1/courses/11/steps/202/answer", json={"answer": None})
        assert result.json()["is_correct"] is None
        assert result.json()["completed"] is True
