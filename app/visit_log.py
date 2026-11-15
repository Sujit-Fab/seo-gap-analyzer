"""
Visit log: records each request to the public pages so there is a record of
when the demo was opened.

Storage follows the same rule as firestore_service:
- Firestore enabled  -> one document per visit in the "visits" collection.
- Otherwise          -> appended to local_data/visits.json.

Optional Telegram notification: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
to get a message when a person (not a bot) opens /docs. At most one message
per visitor IP per hour.

What a visit record can and cannot tell you: it holds the time, path, IP,
browser and referrer. It does not identify the person.

Logging must never break a request, so every failure here is swallowed and
printed to the service log.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.firestore_service import _firestore_client, _use_firestore

LOCAL_VISITS_PATH = Path(__file__).parent.parent / "local_data" / "visits.json"

# Requests the docs page makes on its own; logging them would double-count.
SKIP_PATHS = {"/openapi.json", "/favicon.ico", "/docs/oauth2-redirect", "/robots.txt"}

BOT_MARKERS = (
    "bot", "crawl", "spider", "slurp", "curl", "wget", "python-requests",
    "httpx", "go-http-client", "uptime", "monitor", "preview", "scan",
    "headless", "facebookexternalhit",
)

NOTIFY_PATHS = {"/docs", "/redoc"}
NOTIFY_INTERVAL_SECONDS = 3600
_last_notified: dict[str, float] = {}


def is_bot(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    return not ua or any(marker in ua for marker in BOT_MARKERS)


def client_ip(headers, fallback: str | None) -> str:
    # Cloud Run puts the real visitor address first in X-Forwarded-For.
    forwarded = headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return fallback or "unknown"


def build_record(method: str, path: str, status_code: int, headers, fallback_ip: str | None) -> dict:
    user_agent = headers.get("user-agent", "")
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "status_code": status_code,
        "ip": client_ip(headers, fallback_ip),
        "user_agent": user_agent[:300],
        "referer": headers.get("referer", "")[:300],
        "is_bot": is_bot(user_agent),
    }


def _save(record: dict) -> None:
    if _use_firestore():
        _firestore_client().collection("visits").add(record)
        return

    LOCAL_VISITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if LOCAL_VISITS_PATH.exists():
        existing = json.loads(LOCAL_VISITS_PATH.read_text())
    existing.append(record)
    LOCAL_VISITS_PATH.write_text(json.dumps(existing, indent=2))


def _should_notify(record: dict) -> bool:
    if record["is_bot"] or record["path"] not in NOTIFY_PATHS:
        return False
    now = time.time()
    last = _last_notified.get(record["ip"], 0)
    if now - last < NOTIFY_INTERVAL_SECONDS:
        return False
    _last_notified[record["ip"]] = now
    return True


def _notify(record: dict) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    text = (
        "seo-gap-analyzer demo opened\n"
        f"Path: {record['path']}\n"
        f"Time (UTC): {record['timestamp']}\n"
        f"IP: {record['ip']}\n"
        f"Browser: {record['user_agent'][:120]}\n"
        f"From: {record['referer'] or 'direct'}"
    )
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    urllib.request.urlopen(url, data=data, timeout=3)


def log_visit(method: str, path: str, status_code: int, headers, fallback_ip: str | None) -> None:
    """Record one visit. Never raises."""
    if path in SKIP_PATHS:
        return
    try:
        record = build_record(method, path, status_code, headers, fallback_ip)
        _save(record)
    except Exception as exc:  # noqa: BLE001
        print(f"visit_log: could not save visit: {exc}")
        return
    try:
        if _should_notify(record):
            _notify(record)
    except Exception as exc:  # noqa: BLE001
        print(f"visit_log: could not send notification: {exc}")
