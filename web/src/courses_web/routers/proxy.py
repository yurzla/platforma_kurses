"""Прозрачный прокси web-сервиса к JSON API (любой /api/* запрос)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Request
from starlette.responses import Response

from courses_web.client import forwarded_headers, relay_cookies, send_api

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
    client: httpx.AsyncClient = request.app.state.client
    body = await request.body()
    upstream = await send_api(
        client,
        request.method,
        request.url.path,
        params=list(request.query_params.multi_items()),
        headers=forwarded_headers(request, include_content_type=True),
        content=body,
    )
    response = Response(content=upstream.content, status_code=upstream.status_code)
    for key, value in upstream.headers.items():
        if key.lower() in _DROP_RESPONSE_HEADERS:
            continue
        response.headers[key] = value
    relay_cookies(response, upstream)
    return response
