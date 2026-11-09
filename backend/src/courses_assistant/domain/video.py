"""Разбор ссылок на видео для шагов курса."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlparse

_VIDEO_EXTENSIONS = (".mp4", ".webm", ".ogg", ".ogv", ".mov", ".m4v")


@dataclass(frozen=True, slots=True)
class VideoEmbed:
    """Готовое к рендеру представление видео.

    ``kind``: ``iframe`` (встроенный плеер), ``file`` (прямой медиафайл) или
    ``link`` (фолбэк обычной ссылкой).
    """

    kind: Literal["iframe", "file", "link"]
    src: str


def _host(url: str) -> tuple[str, str, dict[str, list[str]]]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return host, parsed.path, parse_qs(parsed.query)


def _youtube_id(url: str, host: str, path: str, query: dict[str, list[str]]) -> str | None:
    if host == "youtu.be":
        candidate = path.strip("/").split("/")[0]
        return candidate or None
    if host not in {"youtube.com", "youtube-nocookie.com", "m.youtube.com"}:
        return None
    if path == "/watch":
        values = query.get("v") or []
        return values[0] if values else None
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live", "v"}:
        return parts[1]
    return None


def _vk_embed(url: str, host: str, path: str, query: dict[str, list[str]]) -> str | None:
    if host not in {"vk.com", "vkvideo.ru", "m.vk.com"}:
        return None
    if path.endswith("/video_ext.php") or path == "/video_ext.php":
        oid = (query.get("oid") or [""])[0]
        video_id = (query.get("id") or [""])[0]
        if oid and video_id:
            return f"https://vk.com/video_ext.php?oid={oid}&id={video_id}&hd=2"
        return None
    parts = [part for part in path.split("/") if part]
    if parts and parts[0].startswith("video"):
        slug = parts[0][len("video") :].lstrip("-")
        if "_" in slug:
            oid_part, video_part = slug.split("_", 1)
            sign = "-" if parts[0].startswith("video-") else ""
            if oid_part.isdigit() and video_part.isdigit():
                return f"https://vk.com/video_ext.php?oid={sign}{oid_part}&id={video_part}&hd=2"
    return None


def parse_video_url(raw: str | None) -> VideoEmbed | None:
    """Возвращает рендер-описание для http(s)-ссылки или ``None``.

    ``None`` означает, что ссылка небезопасна или не является URL.
    """

    url = (raw or "").strip()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    host, path, query = _host(url)

    youtube_id = _youtube_id(url, host, path, query)
    if youtube_id:
        return VideoEmbed(kind="iframe", src=f"https://www.youtube.com/embed/{youtube_id}")

    vk_src = _vk_embed(url, host, path, query)
    if vk_src:
        return VideoEmbed(kind="iframe", src=vk_src)

    if path.lower().endswith(_VIDEO_EXTENSIONS):
        return VideoEmbed(kind="file", src=url)

    return VideoEmbed(kind="link", src=url)
