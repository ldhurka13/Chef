"""Tests for AI Vibe Recommendations endpoint - top-10 slice + filters"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://diary-watch.preview.emergentagent.com").rstrip("/")
EMAIL = "vibetest2@example.com"
PASSWORD = "Test123!"

TIMEOUT = 180  # AI endpoint is slow


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _post_vibe(headers, body):
    return requests.post(
        f"{BASE_URL}/api/movies/ai-vibe-recommendations",
        json=body,
        headers=headers,
        timeout=TIMEOUT,
    )


def test_default_vibe_returns_at_most_10(headers):
    body = {"brain_power": 50, "mood": 50, "energy": 50, "watch_context": "solo"}
    r = _post_vibe(headers, body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ai_powered") is True
    results = data.get("results", [])
    assert 1 <= len(results) <= 10, f"expected <=10, got {len(results)}"
    for i, m in enumerate(results, start=1):
        assert m.get("vibe_rank") == i, f"vibe_rank mismatch at index {i}: {m.get('vibe_rank')}"
        assert m.get("id")
        assert m.get("title")


def test_feeling_adventurous_filter(headers):
    body = {
        "brain_power": 50, "mood": 50, "energy": 50, "watch_context": "solo",
        "feeling_adventurous": True,
    }
    r = _post_vibe(headers, body)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data.get("results", [])) <= 10
    assert "feeling_adventurous" in (data.get("filters_applied") or [])


def test_only_my_streaming_filter(headers):
    body = {
        "brain_power": 50, "mood": 50, "energy": 50, "watch_context": "solo",
        "only_my_streaming": True,
    }
    r = _post_vibe(headers, body)
    assert r.status_code == 200, r.text
    data = r.json()
    results = data.get("results", [])
    assert len(results) <= 10
    # filters_applied should include only_my_streaming (user has netflix/hulu/prime)
    assert "only_my_streaming" in (data.get("filters_applied") or [])
    for m in results:
        assert "streaming_matches" in m and isinstance(m["streaming_matches"], list)
