"""Клиент к API: проброс заголовков/тела и cookie."""

from __future__ import annotations

from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import Response

_FORWARD_HEADERS = {"cookie", "authorization", "accept", "user-agent"}
_CONTENT_TYPE = "content-type"


def forwarded_headers(request: Request, *, include_content_type: bool = False) -> dict[str, str]:
    allowed = _FORWARD_HEADERS | ({_CONTENT_TYPE} if include_content_type else set())
    return {
        key: value for key, value in request.headers.items() if key.lower() in allowed
    }


def relay_cookies(response: Response, upstream: httpx.Response) -> None:
    for cookie in upstream.headers.get_list("set-cookie"):
        response.headers.append("set-cookie", cookie)


async def send_api(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    **kwargs: Any,
) -> httpx.Response:
    """Запрос к API без сохранения cookie в общем клиенте.

    Cookie сессии пробрасываются вручную (заголовок `Cookie` туда, `Set-Cookie`
    обратно), поэтому jar общего клиента нужно очищать: иначе сессия одного
    браузера утечёт в запросы другого.
    """
    try:
        return await client.request(method, path, **kwargs)
    finally:
        client.cookies.clear()


async def call_api(
    request: Request,
    method: str,
    path: str,
    *,
    content: bytes | None = None,
    json: object | None = None,
) -> httpx.Response:
    client: httpx.AsyncClient = request.app.state.client
    kwargs: dict[str, Any] = {
        "headers": forwarded_headers(request, include_content_type=content is not None)
    }
    if content is not None:
        kwargs["content"] = content
    if json is not None:
        kwargs["json"] = json
    return await send_api(client, method, path, **kwargs)
