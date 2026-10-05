"""Health/readiness роутер."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from courses_assistant.container import Container
from courses_assistant.entrypoints.api.dependencies import get_container

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(response: Response, container: Container = Depends(get_container)) -> dict:
    dependencies: dict[str, str] = {}

    try:
        async with container.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001
        dependencies["postgres"] = f"unavailable: {exc}"

    dependencies["redis"] = "ok" if await container.broker.ping() else "unavailable"

    ready_state = all(value == "ok" for value in dependencies.values())
    if not ready_state:
        response.status_code = 503
    return {"status": "ok" if ready_state else "degraded", "dependencies": dependencies}
