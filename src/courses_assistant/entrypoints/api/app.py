"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from courses_assistant.config import Settings, get_settings
from courses_assistant.container import Container, build_container
from courses_assistant.domain.errors import (
    CourseNotFound,
    ExternalServiceError,
    JobNotFound,
    SessionNotFound,
    UserNotFound,
)
from courses_assistant.entrypoints.api.middleware import RequestContextMiddleware
from courses_assistant.entrypoints.api.routers import chat, health, jobs

logger = structlog.get_logger(__name__)

_NOT_FOUND = (SessionNotFound, JobNotFound, UserNotFound, CourseNotFound)


def _configure_logging(settings: Settings) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ]
    )


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    _configure_logging(settings)
    owns_container = container is None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.container is None:
            app.state.container = build_container(settings)
        settings.require_gigachat_credentials()
        yield
        if app.state.owns_container:
            await app.state.container.close()

    app = FastAPI(title="Courses Assistant API", version="0.1.0", lifespan=lifespan)
    app.state.container = container
    app.state.owns_container = owns_container

    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(jobs.router)

    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    async def external_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("external_service_error", error=str(exc))
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    for exc_class in _NOT_FOUND:
        app.add_exception_handler(exc_class, not_found_handler)
    app.add_exception_handler(ExternalServiceError, external_error_handler)

    return app
