"""FastAPI application factory web-сервиса."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from courses_web.config import Settings, get_settings
from courses_web.middleware import RequestContextMiddleware
from courses_web.routers import pages, proxy

logger = structlog.get_logger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    settings: Settings | None = None, client: httpx.AsyncClient | None = None
) -> FastAPI:
    settings = settings or get_settings()
    owns_client = client is None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.client is None:
            app.state.client = httpx.AsyncClient(base_url=settings.api_base_url, timeout=30.0)
        yield
        if app.state.owns_client:
            await app.state.client.aclose()

    app = FastAPI(
        title="Courses Assistant Web",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.settings = settings
    app.state.client = client
    app.state.owns_client = owns_client

    app.add_middleware(RequestContextMiddleware)
    app.include_router(pages.router)
    app.include_router(proxy.router)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    return app
