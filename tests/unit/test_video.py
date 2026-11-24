"""Тесты разбора видео-ссылок шагов."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from courses_assistant.domain.video import parse_video_url
from courses_assistant.entrypoints.api.schemas import TeacherStepCreate


@pytest.mark.parametrize(
    ("url", "src"),
    [
        ("https://www.youtube.com/watch?v=abc123", "https://www.youtube.com/embed/abc123"),
        ("https://youtu.be/abc123", "https://www.youtube.com/embed/abc123"),
        ("https://youtube.com/shorts/abc123", "https://www.youtube.com/embed/abc123"),
        ("https://www.youtube.com/embed/abc123", "https://www.youtube.com/embed/abc123"),
        (
            "https://vk.com/video-227165132_456239023",
            "https://vk.com/video_ext.php?oid=-227165132&id=456239023&hd=2",
        ),
        (
            "https://vkvideo.ru/video_ext.php?oid=-227165132&id=456239023&hd=2",
            "https://vk.com/video_ext.php?oid=-227165132&id=456239023&hd=2",
        ),
    ],
)
def test_iframe_video_links(url: str, src: str) -> None:
    embed = parse_video_url(url)
    assert embed is not None
    assert embed.kind == "iframe"
    assert embed.src == src


def test_direct_video_file() -> None:
    embed = parse_video_url("https://cdn.example.com/lesson.mp4")
    assert embed is not None
    assert embed.kind == "file"
    assert embed.src == "https://cdn.example.com/lesson.mp4"


def test_unknown_host_falls_back_to_link() -> None:
    embed = parse_video_url("https://example.com/watch/123")
    assert embed is not None
    assert embed.kind == "link"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<b>x</b>",
        "ftp://example.com/v.mp4",
        "не ссылка",
    ],
)
def test_unsafe_video_links_rejected(url: str) -> None:
    assert parse_video_url(url) is None

    with pytest.raises(ValidationError):
        TeacherStepCreate(body="материал", video_url=url)


def test_video_step_requires_video_url() -> None:
    with pytest.raises(ValidationError):
        TeacherStepCreate(body="материал", step_type="video")


def test_video_url_allowed_without_body() -> None:
    payload = TeacherStepCreate(step_type="video", video_url="https://youtu.be/abc123")
    assert payload.video_url == "https://youtu.be/abc123"
