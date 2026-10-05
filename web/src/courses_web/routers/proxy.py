"""Прозрачный прокси web-сервиса к JSON API (любой /api/* запрос)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import Response

from courses_web.client import call_api, relay_cookies, relay_refreshed

router = APIRouter(tags=["proxy"])

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

_DROP_RESPONSE_HEADERS = {
    "content-length",
    "content-encoding",
    "transfer-encoding",
    "connection",
    "keep-alive",
    "set-cookie",
}


@router.api_route("/api/{path:path}", methods=_METHODS)
async def proxy(path: str, request: Request) -> Response:
    body = await request.body()
    upstream = await call_api(
        request,
        request.method,
        request.url.path,
        content=body,
        params=list(request.query_params.multi_items()),
    )
    response = Response(content=upstream.content, status_code=upstream.status_code)
    for key, value in upstream.headers.items():
        if key.lower() in _DROP_RESPONSE_HEADERS:
            continue
        response.headers[key] = value
    relay_cookies(response, upstream)
    relay_refreshed(response, request)
    return response
