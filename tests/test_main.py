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
