"""Tests for unified intent-aware search backend endpoints."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://diary-watch.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


# ---------- /api/search/suggestions ----------
class TestSearchSuggestions:
    def test_suggestions_title_match(self):
        r = requests.get(f"{API}/search/suggestions", params={"q": "inception"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "titles" in data and "people" in data
        assert len(data["titles"]) > 0
        t = data["titles"][0]
        for k in ["id", "media_type", "title", "year", "poster_url"]:
            assert k in t
        assert t["media_type"] in ("movie", "tv")

    def test_suggestions_person_and_titles(self):
        r = requests.get(f"{API}/search/suggestions", params={"q": "christopher nolan"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data["titles"]) > 0
        assert len(data["people"]) >= 1
        p = data["people"][0]
        for k in ["id", "name", "profile_url"]:
            assert k in p

    def test_suggestions_short_query_rejected(self):
        r = requests.get(f"{API}/search/suggestions", params={"q": "a"}, timeout=15)
        assert r.status_code in (400, 422)


# ---------- /api/search/person/{id} ----------
class TestPersonCredits:
    def test_person_nolan(self):
        r = requests.get(f"{API}/search/person/525", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["id"] == 525
        assert "acting" in data and "directing" in data
        assert isinstance(data["acting"], list)
        assert isinstance(data["directing"], list)
        assert len(data["directing"]) > 0, "Nolan should have directing credits"

    def test_person_not_found(self):
        r = requests.get(f"{API}/search/person/999999999", timeout=30)
        assert r.status_code in (404, 500)


# ---------- /api/search/intent ----------
class TestSearchIntent:
    def test_intent_entity(self):
        r = requests.get(f"{API}/search/intent", params={"q": "inception"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["is_entity"] is True
        assert data["best_match"] is not None

    def test_intent_vibe(self):
        r = requests.get(f"{API}/search/intent", params={"q": "something cozy for a rainy day"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data["is_entity"] is False


# ---------- /api/search/vibe ----------
class TestVibeSearch:
    def test_vibe_no_auth_returns_5(self):
        r = requests.post(f"{API}/search/vibe", json={"query": "feeling nostalgic", "limit": 5}, timeout=90)
        assert r.status_code == 200, r.text
        data = r.json()
        results = data.get("results", [])
        assert len(results) == 5, f"Expected exactly 5 results, got {len(results)}"
        for m in results:
            for k in ["id", "title", "poster_url", "vibe_reason"]:
                assert k in m, f"Missing {k} in {m}"

    def test_vibe_with_auth_returns_5(self):
        # Try login first
        login = requests.post(f"{API}/auth/login", json={
            "email": "vibetest2@example.com", "password": "Test123!"
        }, timeout=30)
        if login.status_code != 200:
            pytest.skip(f"Login failed: {login.status_code}")
        token = login.json().get("access_token") or login.json().get("token")
        if not token:
            pytest.skip("No token returned")
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(f"{API}/search/vibe", json={"query": "feeling nostalgic", "limit": 5},
                          headers=headers, timeout=90)
        assert r.status_code == 200
        assert len(r.json().get("results", [])) == 5


# ---------- /api/movies/{id}?media_type=... ----------
class TestMovieDetailsMediaType:
    def test_tv_show_details(self):
        r = requests.get(f"{API}/movies/1399", params={"media_type": "tv"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("media_type") == "tv"
        assert data.get("title") or data.get("name")

    def test_movie_details_still_works(self):
        r = requests.get(f"{API}/movies/27205", params={"media_type": "movie"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "Inception" in (data.get("title", "") or "")

    def test_tv_streaming_no_error(self):
        r = requests.get(f"{API}/movies/1399/streaming", params={"media_type": "tv"}, timeout=30)
        assert r.status_code == 200, r.text
