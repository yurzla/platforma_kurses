"""API-тесты рабочего пространства преподавателя: список собственных курсов."""

from __future__ import annotations

import httpx

from courses_assistant.domain.catalog import (
    CourseDetail,
    LessonSummary,
    SectionSummary,
    StepSummary,
)
from courses_assistant.entrypoints.api.app import create_app
from tests.api.test_api import build_test_container
from tests.fakes import FakeStore, encrypt_test_password


def make_app(store: FakeStore):
    container, _, _ = build_test_container(store)
    app = create_app(settings=container.settings, container=container)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def course(course_id: int, title: str, description: str | None = None) -> CourseDetail:
    step = StepSummary(id=course_id * 10, position=1, step_type="text")
    lesson = LessonSummary(id=course_id, title="Урок", position=1, steps=[step])
    section = SectionSummary(id=course_id, title="Модуль", position=1, lessons=[lesson])
    return CourseDetail(id=course_id, title=title, description=description, sections=[section])


async def _login(ac: httpx.AsyncClient, email: str, password: str = "pw") -> None:
    await ac.post("/api/v1/auth/login", json={"email": email, "password": password})


async def test_teacher_list_only_own_courses() -> None:
    store = FakeStore()
    teacher = store.add_user("t@example.com", "Учитель", encrypt_test_password("pw"), "teacher")
    other = store.add_user("o@example.com", "Другой", encrypt_test_password("pw"), "teacher")
    store.add_course(course(1, "Мой курс"), owner_id=teacher.id)
    store.add_course(course(2, "Чужой курс"), owner_id=other.id)
    ac = make_app(store)
    async with ac:
        await _login(ac, "t@example.com")
        response = await ac.get("/api/v1/teacher/courses")
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [1]
    assert body["total"] == 1
    assert body["items"][0]["lessons_count"] == 1
    assert body["items"][0]["steps_count"] == 1


async def test_teacher_list_search_and_pagination() -> None:
    store = FakeStore()
    teacher = store.add_user("t@example.com", "Учитель", encrypt_test_password("pw"), "teacher")
    for course_id in range(1, 13):
        store.add_course(
            course(course_id, f"Python {course_id}", "Описание"),
            owner_id=teacher.id,
        )
    store.add_course(course(99, "Django", None), owner_id=teacher.id)
    ac = make_app(store)
    async with ac:
        await _login(ac, "t@example.com")

        first = await ac.get(
            "/api/v1/teacher/courses", params={"limit": 10, "offset": 0}
        )
        assert first.json()["total"] == 13
        assert len(first.json()["items"]) == 10

        second = await ac.get(
            "/api/v1/teacher/courses", params={"limit": 10, "offset": 10}
        )
        assert len(second.json()["items"]) == 3

        searched = await ac.get(
            "/api/v1/teacher/courses", params={"search": "django"}
        )
        assert [item["id"] for item in searched.json()["items"]] == [99]
        assert searched.json()["total"] == 1

        empty = await ac.get(
            "/api/v1/teacher/courses", params={"search": "нет такого"}
        )
        assert empty.json()["items"] == []
        assert empty.json()["total"] == 0


async def test_teacher_list_forbidden_for_student() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    ac = make_app(store)
    async with ac:
        await _login(ac, "s@example.com")
        response = await ac.get("/api/v1/teacher/courses")
    assert response.status_code == 403
