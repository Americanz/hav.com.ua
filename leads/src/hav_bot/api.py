"""HTTP-прийом заявки з форми сайту."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from aiohttp import web

from hav_bot.leads import MAX_BODY, origin_allowed, rate_limited, validate

Publish = Callable[[dict], Awaitable[None]]
PUBLISH: web.AppKey[Publish] = web.AppKey("publish")
CONFIGURED: web.AppKey[bool] = web.AppKey("configured")


def json_response(status: int, payload: dict) -> web.Response:
    return web.json_response(payload, status=status, dumps=lambda item: json.dumps(item, ensure_ascii=False))


def create_app(publish: Publish, *, configured: bool) -> web.Application:
    app = web.Application(client_max_size=MAX_BODY)
    app[PUBLISH] = publish
    app[CONFIGURED] = configured
    app.router.add_get("/health", health)
    app.router.add_post("/api/lead", accept_lead)
    return app


async def health(_: web.Request) -> web.Response:
    return json_response(200, {"ok": True})


async def accept_lead(request: web.Request) -> web.Response:
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host")
    if not origin_allowed(request.headers.get("Origin"), host):
        return json_response(403, {"ok": False, "error": "Запит відхилено."})
    if request.content_type != "application/json":
        return json_response(415, {"ok": False, "error": "Некоректний запит."})
    ip = (request.headers.get("X-Real-IP") or request.remote or "unknown").strip()
    if rate_limited(ip):
        return json_response(429, {"ok": False, "error": "Забагато запитів. Спробуйте пізніше."})
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return json_response(400, {"ok": False, "error": "Некоректний запит."})

    lead, error = validate(data)
    if error or lead is None:
        return json_response(400, {"ok": False, "error": error or "Некоректний запит."})
    if lead.get("honeypot"):
        return json_response(200, {"ok": True})
    if not request.app[CONFIGURED]:
        print("telegram env is not set", flush=True)
        return json_response(503, {"ok": False, "error": "Прийом заявок тимчасово недоступний."})
    try:
        await request.app[PUBLISH](lead)
    except Exception as exc:
        print(f"lead send failed: {type(exc).__name__}", flush=True)
        return json_response(502, {"ok": False, "error": "Не вдалося надіслати заявку. Спробуйте пізніше."})
    print("lead sent", flush=True)
    return json_response(200, {"ok": True})
