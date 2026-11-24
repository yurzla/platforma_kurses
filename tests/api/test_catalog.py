"""API-тесты каталога: курсы, шаги, ответы, прогресс."""

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
        "/api/v1/auth/login", json={"email": "s@example.com", "password": "pw"}
    )


async def test_catalog_requires_login() -> None:
    store = FakeStore()
    store.add_course(build_course())
    ac = make_app(store)
    async with ac:
        assert (await ac.get("/api/v1/courses")).status_code == 401


async def test_course_and_step_flow() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(build_course())
    store.answer_keys[101] = CHOICE_KEY
    ac = make_app(store)
    async with ac:
        await _login(ac)

        courses = await ac.get("/api/v1/courses")
        assert courses.status_code == 200
        assert courses.json()["items"][0]["id"] == 10
        assert courses.json()["items"][0]["steps_count"] == 1
        assert courses.json()["total"] == 1
        assert courses.json()["limit"] == 50
        assert courses.json()["offset"] == 0

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


async def test_list_courses_enrolled_filter() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(build_course())
    other_step = StepSummary(id=202, position=1, step_type="text")
    other_lesson = LessonSummary(id=12, title="Урок", position=1, steps=[other_step])
    other_section = SectionSummary(id=2, title="Модуль", position=1, lessons=[other_lesson])
    store.add_course(CourseDetail(id=11, title="Other", sections=[other_section]))
    ac = make_app(store)
    async with ac:
        await _login(ac)

        all_courses = await ac.get("/api/v1/courses")
        assert {c["id"] for c in all_courses.json()["items"]} == {10, 11}
        assert all_courses.json()["total"] == 2

        none_enrolled = await ac.get("/api/v1/courses", params={"enrolled": "true"})
        assert none_enrolled.json()["items"] == []
        assert none_enrolled.json()["total"] == 0

        await ac.post("/api/v1/courses/10/steps/101/answer", json={"answer": None})

        enrolled = await ac.get("/api/v1/courses", params={"enrolled": "true"})
        assert [c["id"] for c in enrolled.json()["items"]] == [10]
        assert enrolled.json()["total"] == 1


async def test_list_courses_pagination() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    for course_id in range(1, 26):
        step = StepSummary(id=course_id * 10, position=1, step_type="text")
        lesson = LessonSummary(id=course_id, title=f"Урок {course_id}", position=1, steps=[step])
        section = SectionSummary(id=course_id, title="Модуль", position=1, lessons=[lesson])
        store.add_course(
            CourseDetail(id=course_id, title=f"Курс {course_id}", sections=[section])
        )
    ac = make_app(store)
    async with ac:
        await _login(ac)

        first = await ac.get("/api/v1/courses", params={"limit": 10, "offset": 0})
        assert first.json()["total"] == 25
        assert first.json()["limit"] == 10
        assert first.json()["offset"] == 0
        assert len(first.json()["items"]) == 10
        assert first.json()["items"][0]["id"] == 1
        assert first.json()["items"][-1]["id"] == 10

        last = await ac.get("/api/v1/courses", params={"limit": 10, "offset": 20})
        assert len(last.json()["items"]) == 5
        assert last.json()["items"][0]["id"] == 21

        beyond = await ac.get("/api/v1/courses", params={"limit": 10, "offset": 40})
        assert beyond.json()["items"] == []
        assert beyond.json()["total"] == 25


async def test_manual_step_completion() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
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


def _course_with_step(course_id: int, title: str, description: str | None, step_id: int):
    step = StepSummary(id=step_id, position=1, step_type="text")
    lesson = LessonSummary(id=course_id, title="Урок", position=1, steps=[step])
    section = SectionSummary(id=course_id, title="Модуль", position=1, lessons=[lesson])
    return CourseDetail(id=course_id, title=title, description=description, sections=[section])


async def test_course_search_by_title_and_description() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(_course_with_step(1, "Python Basics", "Для начинающих", 101))
    store.add_course(_course_with_step(2, "Django", "Веб на PYTHON", 201))
    store.add_course(_course_with_step(3, "Go", "Язык серверов", 301))
    ac = make_app(store)
    async with ac:
        await _login(ac)

        by_title = await ac.get("/api/v1/courses", params={"search": "python"})
        assert {c["id"] for c in by_title.json()["items"]} == {1, 2}
        assert by_title.json()["total"] == 2

        by_description = await ac.get("/api/v1/courses", params={"search": "серверов"})
        assert [c["id"] for c in by_description.json()["items"]] == [3]
        assert by_description.json()["total"] == 1

        lowercase = await ac.get("/api/v1/courses", params={"search": "PYTHON"})
        assert {c["id"] for c in lowercase.json()["items"]} == {1, 2}

        blank = await ac.get("/api/v1/courses", params={"search": "   "})
        assert blank.json()["total"] == 3


async def test_course_search_no_matches() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(_course_with_step(1, "Python", None, 101))
    ac = make_app(store)
    async with ac:
        await _login(ac)
        response = await ac.get("/api/v1/courses", params={"search": "нет такого"})
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


async def test_course_search_combines_with_enrollment_and_pagination() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    user_id = next(iter(store.users))
    for course_id in range(1, 13):
        store.add_course(_course_with_step(course_id, f"Python {course_id}", None, course_id * 10))
    store.add_course(_course_with_step(99, "Django", None, 990))
    for course_id in (1, 2, 3):
        store.progress[(user_id, course_id * 10)] = "passed"
    ac = make_app(store)
    async with ac:
        await _login(ac)

        page = await ac.get(
            "/api/v1/courses",
            params={"search": "python", "limit": 5, "offset": 0},
        )
        assert page.json()["total"] == 12
        assert len(page.json()["items"]) == 5

        enrolled = await ac.get(
            "/api/v1/courses", params={"search": "python", "enrolled": "true"}
        )
        assert {c["id"] for c in enrolled.json()["items"]} == {1, 2, 3}
        assert enrolled.json()["total"] == 3

        enrolled_other = await ac.get(
            "/api/v1/courses", params={"search": "django", "enrolled": "true"}
        )
        assert enrolled_other.json()["items"] == []
        assert enrolled_other.json()["total"] == 0


async def test_course_search_treats_wildcards_literally() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(_course_with_step(1, "100% Python", None, 101))
    store.add_course(_course_with_step(2, "Python", None, 201))
    store.add_course(_course_with_step(3, "under_score", None, 301))
    ac = make_app(store)
    async with ac:
        await _login(ac)

        percent = await ac.get("/api/v1/courses", params={"search": "100%"})
        assert [c["id"] for c in percent.json()["items"]] == [1]

        underscore = await ac.get("/api/v1/courses", params={"search": "under_"})
        assert [c["id"] for c in underscore.json()["items"]] == [3]


async def test_step_video_embed() -> None:
    store = FakeStore()
    store.add_user("s@example.com", "Студент", encrypt_test_password("pw"), "student")
    store.add_course(build_course())
    store.step_video_urls[101] = "https://youtu.be/abc123"
    ac = make_app(store)
    async with ac:
        await _login(ac)
        response = await ac.get("/api/v1/courses/10/steps/101")
    assert response.status_code == 200
    body = response.json()
    assert body["video_url"] == "https://youtu.be/abc123"
    assert body["video"] == {
        "kind": "iframe",
        "src": "https://www.youtube.com/embed/abc123",
    }

    store.step_video_urls[101] = "https://example.com/clip.mp4"
    ac = make_app(store)
    async with ac:
        await _login(ac)
        response = await ac.get("/api/v1/courses/10/steps/101")
    assert response.json()["video"]["kind"] == "file"

    store.step_video_urls[101] = "https://example.com/watch"
    ac = make_app(store)
    async with ac:
        await _login(ac)
        response = await ac.get("/api/v1/courses/10/steps/101")
    assert response.json()["video"]["kind"] == "link"
