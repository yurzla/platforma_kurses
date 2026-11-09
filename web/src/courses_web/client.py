"""Клиент к API: проброс заголовков/тела и cookie, авто-refresh access-токена."""

from __future__ import annotations

from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import Response

from courses_web.config import Settings

_FORWARD_HEADERS = {"cookie", "authorization", "accept", "user-agent"}
_CONTENT_TYPE = "content-type"
_REFRESH_PATH = "/api/v1/auth/refresh"


def forwarded_headers(request: Request, *, include_content_type: bool = False) -> dict[str, str]:
    allowed = _FORWARD_HEADERS | ({_CONTENT_TYPE} if include_content_type else set())
    return {
        key: value for key, value in request.headers.items() if key.lower() in allowed
    }


def relay_cookies(response: Response, upstream: httpx.Response) -> None:
    for cookie in upstream.headers.get_list("set-cookie"):
        response.headers.append("set-cookie", cookie)


def relay_refreshed(response: Response, request: Request) -> None:
    """Ретранслирует cookie, полученные при авто-refresh, в ответ браузеру."""
    for cookie in getattr(request.state, "refreshed_cookies", []):
        response.headers.append("set-cookie", cookie)


def _remember_refreshed(request: Request, cookies: list[str]) -> None:
    existing: list[str] = getattr(request.state, "refreshed_cookies", [])
    request.state.refreshed_cookies = existing + cookies


def _cookie_header_with(cookie_header: str, set_cookie_headers: list[str]) -> str:
    jar: dict[str, str] = {}
    for part in cookie_header.split(";"):
        name, sep, value = part.strip().partition("=")
        if sep:
            jar[name] = value
    for header in set_cookie_headers:
        pair, _, _rest = header.partition(";")
        name, sep, value = pair.strip().partition("=")
        if not sep:
            continue
        if value == "":
            jar.pop(name, None)
        else:
            jar[name] = value
    return "; ".join(f"{name}={value}" for name, value in jar.items())


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


async def _refresh(request: Request, settings: Settings, client: httpx.AsyncClient) -> bool:
    resp = await send_api(
        client,
        "POST",
        _REFRESH_PATH,
        headers={"cookie": request.headers.get("cookie", "")},
    )
    if resp.status_code != 200:
        return False
    set_cookies = resp.headers.get_list("set-cookie")
    _remember_refreshed(request, set_cookies)
    request.state.merged_cookie = _cookie_header_with(
        request.headers.get("cookie", ""), set_cookies
    )
    return True


async def call_api(
    request: Request,
    method: str,
    path: str,
    *,
    content: bytes | None = None,
    json: object | None = None,
    params: list[tuple[str, str]] | None = None,
) -> httpx.Response:
    settings: Settings = request.app.state.settings
    client: httpx.AsyncClient = request.app.state.client
    headers = forwarded_headers(request, include_content_type=content is not None)
    merged_cookie = getattr(request.state, "merged_cookie", None)
    if merged_cookie:
        headers["cookie"] = merged_cookie
    kwargs: dict[str, Any] = {"headers": headers}
    if content is not None:
        kwargs["content"] = content
    if json is not None:
        kwargs["json"] = json
    if params is not None:
        kwargs["params"] = params
    response = await send_api(client, method, path, **kwargs)

    has_refresh = settings.refresh_cookie in request.cookies
    if response.status_code == 401 and has_refresh and path != _REFRESH_PATH:
        if await _refresh(request, settings, client):
            retry = {key: value for key, value in kwargs.items() if key != "headers"}
            retry["headers"] = {
                **kwargs["headers"],
                "cookie": request.state.merged_cookie,
            }
            response = await send_api(client, method, path, **retry)
    return response
