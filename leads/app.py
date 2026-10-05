"""Приймає заявку з форми сайту і надсилає її в Telegram."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 16_384
WINDOW_SEC = 15 * 60
LIMIT = 5
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clean(value: object) -> str:
    text = str(value or "")
    return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32).strip()


def telegram_config() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id


def rate_limited(ip: str) -> bool:
    now = time.monotonic()
    with _lock:
        if len(_hits) > 10_000:
            _hits.clear()
        hits = [stamp for stamp in _hits.get(ip, []) if now - stamp < WINDOW_SEC]
        if len(hits) >= LIMIT:
            _hits[ip] = hits
            return True
        hits.append(now)
        _hits[ip] = hits
        return False


def reset_limits() -> None:
    with _lock:
        _hits.clear()


def validate(data: object) -> tuple[dict | None, str | None]:
    if not isinstance(data, dict):
        return None, "Некоректний запит."
    if clean(data.get("hp")):
        return {"honeypot": True}, None

    name = clean(data.get("name"))
    email = clean(data.get("email"))
    phone = clean(data.get("phone"))
    message = clean(data.get("message"))

    if not 1 <= len(name) <= 80 or not re.search(r"\w", name, re.UNICODE):
        return None, "Вкажіть ім'я."
    if not EMAIL_RE.match(email) or len(email) > 120:
        return None, "Вкажіть коректний email."
    if len(phone) > 40:
        return None, "Телефон занадто довгий."
    if len(message) > 4000:
        return None, "Повідомлення занадто довге."
    topic = clean(data.get("topic"))
    if topic not in {"", "ERP", "BAS", "Odoo"}:
        topic = ""
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "topic": topic,
    }, None


def build_text(lead: dict) -> str:
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "<b>Нова заявка з hav.com.ua</b>",
        f"<i>{when}</i>",
        "",
        f"<b>Ім'я:</b> {esc(lead['name'])}",
        f"<b>Email:</b> {esc(lead['email'])}",
    ]
    if lead.get("topic"):
        lines.append(f"<b>Напрямок:</b> {esc(lead['topic'])}")
    if lead["phone"]:
        lines.append(f"<b>Телефон:</b> {esc(lead['phone'])}")
    if lead["message"]:
        lines.extend(["", esc(lead["message"])])
    return "\n".join(lines)


def send_to_telegram(lead: dict) -> None:
    token, chat_id = telegram_config()
    if not token or not chat_id:
        raise RuntimeError("telegram is not configured")
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": build_text(lead),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        print(f"telegram http {exc.code}", flush=True)
        raise RuntimeError("telegram rejected the message") from exc
    if not body.get("ok"):
        print("telegram response was not ok", flush=True)
        raise RuntimeError("telegram rejected the message")


def origin_allowed(origin: str | None, host: str | None) -> bool:
    if not origin:
        return True
    if not host:
        return False
    scheme, _, netloc = origin.partition("://")
    if scheme not in {"http", "https"} or not netloc:
        return False
    return netloc == host


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/health":
            self._json(200, {"ok": True})
            return
        self._json(404, {"ok": False, "error": "Не знайдено."})

    def _discard_body(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return
        remaining = min(max(length, 0), MAX_BODY)
        while remaining:
            chunk = self.rfile.read(min(remaining, 8192))
            if not chunk:
                break
            remaining -= len(chunk)

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/lead":
            self._discard_body()
            self._json(404, {"ok": False, "error": "Не знайдено."})
            return
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host")
        if not origin_allowed(self.headers.get("Origin"), host):
            self._discard_body()
            self._json(403, {"ok": False, "error": "Запит відхилено."})
            return
        ctype = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if ctype != "application/json":
            self._json(415, {"ok": False, "error": "Некоректний запит."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._json(400, {"ok": False, "error": "Некоректний запит."})
            return
        ip = (self.headers.get("X-Real-IP") or self.client_address[0] or "").strip()
        if rate_limited(ip or "unknown"):
            self._json(429, {"ok": False, "error": "Забагато запитів. Спробуйте пізніше."})
            return
        try:
            data = json.loads(self.rfile.read(length).decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "Некоректний запит."})
            return

        lead, error = validate(data)
        if error or lead is None:
            self._json(400, {"ok": False, "error": error or "Некоректний запит."})
            return
        if lead.get("honeypot"):
            self._json(200, {"ok": True})
            return
        token, chat_id = telegram_config()
        if not token or not chat_id:
            print("telegram env is not set", flush=True)
            self._json(503, {"ok": False, "error": "Прийом заявок тимчасово недоступний."})
            return
        try:
            send_to_telegram(lead)
        except (RuntimeError, urllib.error.URLError, TimeoutError):
            self._json(502, {"ok": False, "error": "Не вдалося надіслати заявку. Спробуйте пізніше."})
            return
        print("lead sent", flush=True)
        self._json(200, {"ok": True})

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"leads listening on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
