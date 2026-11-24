"""Тесты подбора курсов по эмбеддингам."""

from __future__ import annotations

from courses_assistant.application.recommendations import rank_courses
from courses_assistant.domain.catalog import CourseSummary
from courses_assistant.domain.models import LearningPreferences
from courses_assistant.domain.recommender import (
    CourseMatch,
    build_recommended_courses_section,
    looks_like_course_query,
    select_courses,
)
from tests.fakes import FakeEmbedder, FakeLLM, FakeStore, InMemoryCourseRecommender


def _match(course_id: int, score: float, title: str = "Курс") -> CourseMatch:
    return CourseMatch(course_id=course_id, title=title, description=None, score=score)


def test_intent_detected_for_course_questions() -> None:
    assert looks_like_course_query("какие курсы по js есть?")
    assert looks_like_course_query("какой курс посоветуешь")
    assert looks_like_course_query("посоветуй курс")
    assert looks_like_course_query("с чего начать изучение")


def test_intent_ignored_for_content_questions() -> None:
    assert not looks_like_course_query("как устроен цикл for?")
    assert not looks_like_course_query("объясни замыкания")


def test_select_courses_applies_margin_and_top_k() -> None:
    matches = [
        _match(1, 0.90),
        _match(2, 0.88),
        _match(3, 0.85),
        _match(4, 0.50),
    ]
    selected = select_courses(matches, top_k=5, margin=0.06, min_score=0.0)
    assert [m.course_id for m in selected] == [1, 2, 3]


def test_select_courses_respects_top_k() -> None:
    matches = [_match(i, 0.9) for i in range(1, 6)]
    selected = select_courses(matches, top_k=2, margin=0.1, min_score=0.0)
    assert [m.course_id for m in selected] == [1, 2]


def test_select_courses_respects_min_score() -> None:
    matches = [_match(1, 0.90), _match(2, 0.40)]
    selected = select_courses(matches, top_k=5, margin=0.5, min_score=0.6)
    assert [m.course_id for m in selected] == [1]


def test_select_courses_empty() -> None:
    assert select_courses([], top_k=5, margin=0.1, min_score=0.0) == []
    assert select_courses([_match(1, 0.9)], top_k=0, margin=0.1, min_score=0.0) == []


def test_build_recommended_courses_section() -> None:
    matches = [
        CourseMatch(course_id=3, title="JS", description="  Курс   про JS  ", score=0.9),
        CourseMatch(course_id=10, title="Frontend", description=None, score=0.8),
    ]
    text = build_recommended_courses_section(matches, description_limit=100)
    assert text == "- [«JS»](/courses/3) — Курс про JS\n- [«Frontend»](/courses/10)"


async def test_rank_courses_expands_and_selects() -> None:
    store = FakeStore()
    store.recommendations = [
        _match(3, 0.9, "JS"),
        _match(10, 0.85, "Frontend"),
        _match(12, 0.4, "Go"),
    ]
    llm = FakeLLM(default="javascript, react")
    result = await rank_courses(
        "какие курсы по js есть?",
        llm=llm,
        embedder=FakeEmbedder(),
        recommender=InMemoryCourseRecommender(store),
        model_name="nomic-embed-text",
        top_k=5,
        margin=0.1,
        min_score=0.0,
        candidate_limit=20,
    )
    assert [m.course_id for m in result] == [3, 10]
    assert len(llm.calls) == 1


async def test_rank_courses_embeds_saved_preferences() -> None:
    embedder = FakeEmbedder()
    await rank_courses(
        "Какой курс выбрать?",
        llm=FakeLLM(default="python"),
        embedder=embedder,
        recommender=InMemoryCourseRecommender(FakeStore()),
        model_name="nomic-embed-text",
        top_k=5,
        margin=0.1,
        min_score=0.0,
        candidate_limit=20,
        preferences=LearningPreferences(
            user_id=1,
            interests="анализ данных",
            goals="сменить профессию",
            preferred_level="beginner",
        ),
    )

    assert "Интересы: анализ данных" in embedder.calls[0]
    assert "Цели обучения: сменить профессию" in embedder.calls[0]
    assert "Желаемый уровень: beginner" in embedder.calls[0]


async def test_rank_courses_excludes_completed_courses_but_uses_their_context() -> None:
    store = FakeStore()
    store.recommendations = [_match(1, 0.9, "Пройденный"), _match(2, 0.85, "Новый")]
    embedder = FakeEmbedder()
    result = await rank_courses(
        "Что пройти дальше?",
        llm=FakeLLM(default="python"),
        embedder=embedder,
        recommender=InMemoryCourseRecommender(store),
        model_name="nomic-embed-text",
        top_k=5,
        margin=0.1,
        min_score=0.0,
        candidate_limit=20,
        completed_courses=[CourseSummary(id=1, title="Пройденный", description="Основы Python")],
    )

    assert [course.course_id for course in result] == [2]
    assert "Пройденный курс: Пройденный. Основы Python" in embedder.calls[0]
