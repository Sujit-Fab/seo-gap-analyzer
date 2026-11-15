"""
Tests run against the mock LLM path (no OPENAI_API_KEY needed) and the
local-file storage fallback (no Firebase credentials needed) — so this
suite runs anywhere, including in a take-home assignment review.
"""

import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.firestore_service import LOCAL_STORE_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_local_store():
    """Each test starts with a clean local data file."""
    if LOCAL_STORE_PATH.exists():
        LOCAL_STORE_PATH.unlink()
    yield
    if LOCAL_STORE_PATH.parent.exists():
        shutil.rmtree(LOCAL_STORE_PATH.parent, ignore_errors=True)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_structured_gaps():
    payload = {
        "content": "This article explains what a CDN is and why websites use one for speed.",
        "target_keyword": "best CDN for small business",
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["target_keyword"] == payload["target_keyword"]
    assert isinstance(body["gaps"], list)
    assert len(body["gaps"]) > 0
    assert "analysis_id" in body
    # Each gap should match the schema
    for gap in body["gaps"]:
        assert "topic" in gap
        assert "why_it_matters" in gap
        assert gap["priority"] in ("high", "medium", "low")


def test_analyze_rejects_short_content():
    payload = {"content": "too short", "target_keyword": "seo"}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_get_analysis_after_saving():
    payload = {
        "content": "A long enough piece of sample content about email marketing tools.",
        "target_keyword": "email marketing tools",
    }
    create_response = client.post("/analyze", json=payload)
    analysis_id = create_response.json()["analysis_id"]

    fetch_response = client.get(f"/analyze/{analysis_id}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["analysis_id"] == analysis_id


def test_get_nonexistent_analysis_returns_404():
    response = client.get("/analyze/does-not-exist")
    assert response.status_code == 404


# --- visit log ---------------------------------------------------------

import json

from app import visit_log
from app.visit_log import LOCAL_VISITS_PATH

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/157.0 Safari/537.36"


def _visits():
    return json.loads(LOCAL_VISITS_PATH.read_text()) if LOCAL_VISITS_PATH.exists() else []


def test_visit_is_recorded_with_forwarded_ip():
    client.get(
        "/docs",
        headers={
            "user-agent": BROWSER_UA,
            "x-forwarded-for": "203.0.113.7, 10.0.0.1",
            "referer": "https://github.com/Sujit-Fab/seo-gap-analyzer",
        },
    )
    visits = _visits()
    assert len(visits) == 1
    visit = visits[0]
    assert visit["path"] == "/docs"
    assert visit["status_code"] == 200
    assert visit["ip"] == "203.0.113.7"
    assert visit["is_bot"] is False
    assert visit["referer"].startswith("https://github.com/")
    assert visit["timestamp"].endswith("+00:00")


def test_openapi_request_is_not_recorded():
    client.get("/openapi.json", headers={"user-agent": BROWSER_UA})
    assert _visits() == []


def test_bot_visit_is_flagged():
    client.get("/", headers={"user-agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"})
    assert _visits()[0]["is_bot"] is True


def test_failed_requests_are_recorded_too():
    client.get("/analyze/does-not-exist", headers={"user-agent": BROWSER_UA})
    assert _visits()[0]["status_code"] == 404


def test_logging_failure_does_not_break_the_request(monkeypatch):
    def boom(record):
        raise RuntimeError("storage is down")

    monkeypatch.setattr(visit_log, "_save", boom)
    response = client.get("/", headers={"user-agent": BROWSER_UA})
    assert response.status_code == 200


def test_notification_only_for_people_on_docs_and_throttled(monkeypatch):
    sent = []
    monkeypatch.setattr(visit_log, "_notify", lambda record: sent.append(record["path"]))
    visit_log._last_notified.clear()
    human = {"user-agent": BROWSER_UA, "x-forwarded-for": "198.51.100.9"}

    client.get("/", headers=human)                      # not a notify path
    client.get("/docs", headers={"user-agent": "curl/8.0"})  # bot
    client.get("/docs", headers=human)                  # notifies
    client.get("/docs", headers=human)                  # throttled
    assert sent == ["/docs"]


def test_no_notification_attempt_without_telegram_settings(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr(visit_log.urllib.request, "urlopen", no_network)
    visit_log._last_notified.clear()
    response = client.get("/docs", headers={"user-agent": BROWSER_UA})
    assert response.status_code == 200
