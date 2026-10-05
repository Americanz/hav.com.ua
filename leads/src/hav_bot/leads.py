"""Валідація заявки і текст повідомлення в Telegram."""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone

MAX_BODY = 16_384
WINDOW_SEC = 15 * 60
LIMIT = 5
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STATUS_RE = re.compile(r"<b>Статус:</b> [^\n]+")
TOPICS = {"", "ERP", "BAS", "Odoo"}

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clean(value: object) -> str:
    text = str(value or "")
    return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32).strip()


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


def origin_allowed(origin: str | None, host: str | None) -> bool:
    if not origin:
        return True
    if not host:
        return False
    scheme, _, netloc = origin.partition("://")
    if scheme not in {"http", "https"} or not netloc:
        return False
    return netloc == host


def check_name(name: str) -> str | None:
    if not 1 <= len(name) <= 80 or not re.search(r"\w", name, re.UNICODE):
        return "Вкажіть ім'я."
    return None


def validate(data: object) -> tuple[dict | None, str | None]:
    if not isinstance(data, dict):
        return None, "Некоректний запит."
    if clean(data.get("hp")):
        return {"honeypot": True}, None

    name = clean(data.get("name"))
    email = clean(data.get("email"))
    phone = clean(data.get("phone"))
    message = clean(data.get("message"))

    name_problem = check_name(name)
    if name_problem:
        return None, name_problem
    if not EMAIL_RE.match(email) or len(email) > 120:
        return None, "Вкажіть коректний email."
    if len(phone) > 40:
        return None, "Телефон занадто довгий."
    if len(message) > 4000:
        return None, "Повідомлення занадто довге."
    topic = clean(data.get("topic"))
    if topic not in TOPICS:
        topic = ""
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "topic": topic,
    }, None


def build_text(lead: dict, *, source: str = "сайт", status: str | None = "Нова") -> str:
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "<b>Нова заявка з hav.com.ua</b>",
        f"<i>{when}</i>",
        "",
        f"<b>Ім'я:</b> {esc(lead['name'])}",
        f"<b>Email:</b> {esc(lead['email'])}",
        f"<b>Джерело:</b> {esc(source)}",
    ]
    if lead.get("topic"):
        lines.append(f"<b>Напрямок:</b> {esc(lead['topic'])}")
    if lead.get("phone"):
        lines.append(f"<b>Телефон:</b> {esc(lead['phone'])}")
    if lead.get("message"):
        lines.extend(["", esc(lead["message"])])
    if status:
        lines.extend(["", f"<b>Статус:</b> {esc(status)}"])
    return "\n".join(lines)


def with_status(text: str, status: str) -> str:
    line = f"<b>Статус:</b> {esc(status)}"
    if STATUS_RE.search(text):
        return STATUS_RE.sub(line, text, count=1)
    return f"{text}\n\n{line}"
