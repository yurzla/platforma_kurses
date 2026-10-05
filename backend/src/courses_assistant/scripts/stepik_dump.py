"""Выгрузка курсов Stepik в JSON-дамп.

Пример: python -m courses_assistant.scripts.stepik_dump --output stepik_dump
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx
import typer

app = typer.Typer(help="Выгрузка курсов Stepik в JSON.")

COURSE_URLS = [
    "https://stepik.org/course/67/",
    "https://stepik.org/course/100707/",
    "https://stepik.org/course/63085/",
    "https://stepik.org/course/266048/",
    "https://stepik.org/course/268534/",
    "https://stepik.org/course/292537/",
    "https://stepik.org/course/264409/",
    "https://stepik.org/course/182715/",
    "https://stepik.org/course/210768/",
    "https://stepik.org/course/209247/",
    "https://stepik.org/course/187230/",
    "https://stepik.org/course/129/",
    "https://stepik.org/course/287409/",
    "https://stepik.org/course/293290/",
    "https://stepik.org/course/215591/",
    "https://stepik.org/course/244364/",
    "https://stepik.org/course/240191/",
]

BASE = "https://stepik.org/api"


def _course_ids() -> list[int]:
    ids: list[int] = []
    for url in COURSE_URLS:
        match = re.search(r"(\d+)/?$", url)
        if match:
            ids.append(int(match.group(1)))
    return ids


def _get(client: httpx.Client, path: str, token: str, **params) -> list[dict]:
    url = f"{BASE}/{path}"
    results: list[dict] = []
    while url:
        try:
            response = client.get(
                url, headers={"Authorization": f"Bearer {token}"}, params=params
            )
        except httpx.HTTPError as exc:
            typer.echo(f"  ! {path}: сеть упала ({exc})")
            return results
        if response.status_code != 200:
            typer.echo(f"  ! {path} -> {response.status_code}: {response.text[:200]}")
            return results
        data = response.json()
        key = path.split("/")[0]
        results.extend(data.get(key, []))
        url = data.get("meta", {}).get("next")
        params = {}
        time.sleep(0.2)
    return results


def _dump_course(client: httpx.Client, token: str, cid: int, out: Path) -> None:
    typer.echo(f"\n=== Курс {cid} ===")
    courses = _get(client, f"courses/{cid}", token)
    if not courses:
        typer.echo("  курс не найден или закрыт")
        return
    course = courses[0]
    typer.echo(f"  {course.get('title')}")

    sections = _get(client, "sections", token, course=cid)
    units = _get(client, "units", token, course=cid)
    lesson_ids = list({unit["lesson"] for unit in units})

    result: dict = {
        "course": course,
        "sections": sections,
        "units": units,
        "lessons": {},
        "steps": {},
    }
    for lesson_id in lesson_ids:
        lesson = _get(client, f"lessons/{lesson_id}", token)
        if lesson:
            result["lessons"][lesson_id] = lesson[0]
        for step in _get(client, "steps", token, lesson=lesson_id):
            result["steps"][step["id"]] = step

    path = out / f"course_{cid}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"  -> {path} (уроков: {len(lesson_ids)}, шагов: {len(result['steps'])})")


@app.command()
def main(  # noqa: PLR0913
    output: Path = typer.Option(Path("stepik_dump"), "--output", "-o"),
    token: str = typer.Option("", "--token", envvar="access_token"),
    course_ids: str = typer.Option("", "--courses", help="через запятую; по умолчанию все"),
) -> None:
    if not token:
        raise typer.BadParameter("Не задан access_token (--token или env access_token).")
    output.mkdir(parents=True, exist_ok=True)
    ids = [int(x) for x in course_ids.split(",") if x.strip()] if course_ids else _course_ids()
    with httpx.Client(timeout=30) as client:
        for cid in ids:
            try:
                _dump_course(client, token, cid, output)
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Курс {cid} упал: {exc}")


if __name__ == "__main__":
    app()
