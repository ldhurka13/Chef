"""
E2E integration tests for the Starter Library Onboarding feature.

Tests the following endpoints against the deployed backend:
- GET /api/onboarding/eligibility
- GET /api/onboarding/popular-movies
- POST /api/onboarding/skip
- POST /api/onboarding/complete
- POST /api/user/watch-history (used by onboarding to add movies)

Uses test credentials from /app/memory/test_credentials.md
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://diary-watch.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEST_EMAIL = "vibetest2@example.com"
TEST_PASSWORD = "Test123!"


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Login and return auth token"""
    resp = api_client.post(
        f"{API}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ---------- /api/onboarding/eligibility ----------
class TestOnboardingEligibility:
    def test_eligibility_requires_auth(self, api_client):
        # No auth header -> should be 401 (or 403)
        resp = api_client.get(f"{API}/onboarding/eligibility")
        assert resp.status_code in (401, 403), f"expected 401/403 got {resp.status_code}: {resp.text}"

    def test_eligibility_returns_full_schema(self, api_client, auth_headers):
        resp = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers)
        assert resp.status_code == 200, resp.text

        data = resp.json()
        # All required fields present
        for f in [
            "eligible",
            "diary_count",
            "watchlist_count",
            "onboarding_skipped",
            "onboarding_completed",
            "minimum_required",
            "movies_needed",
        ]:
            assert f in data, f"Missing field: {f}"

        # Correct minimum
        assert data["minimum_required"] == 5, f"minimum_required should be 5, got {data['minimum_required']}"

        # Type checks
        assert isinstance(data["eligible"], bool)
        assert isinstance(data["diary_count"], int)
        assert isinstance(data["watchlist_count"], int)
        assert isinstance(data["movies_needed"], int)

        # Consistency: movies_needed should equal max(0, 5 - diary_count)
        expected_needed = max(0, 5 - data["diary_count"])
        assert data["movies_needed"] == expected_needed, (
            f"movies_needed={data['movies_needed']} but expected {expected_needed} "
            f"(diary_count={data['diary_count']})"
        )

        # Consistency: eligible == diary_count < 5
        assert data["eligible"] == (data["diary_count"] < 5), (
            f"eligible={data['eligible']} but diary_count={data['diary_count']}"
        )


# ---------- /api/onboarding/popular-movies ----------
class TestPopularMovies:
    def test_popular_movies_returns_list(self, api_client):
        # This endpoint doesn't require auth in current code
        resp = api_client.get(f"{API}/onboarding/popular-movies", timeout=60)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_popular_movies_returns_expected_count(self, api_client):
        resp = api_client.get(f"{API}/onboarding/popular-movies", timeout=60)
        assert resp.status_code == 200
        results = resp.json().get("results", [])
        # Router aims for 30 movies (20 popular + 10 shuffled)
        assert 20 <= len(results) <= 30, f"Expected 20-30 movies, got {len(results)}"

    def test_popular_movies_shape(self, api_client):
        resp = api_client.get(f"{API}/onboarding/popular-movies", timeout=60)
        assert resp.status_code == 200
        results = resp.json().get("results", [])
        assert len(results) > 0, "No movies returned"
        first = results[0]
        # TMDB movie schema
        assert "id" in first
        assert "title" in first
        # poster_url should be added by router when poster_path exists
        with_poster = [m for m in results if m.get("poster_path")]
        assert len(with_poster) > 0, "No movies with poster_path"
        for m in with_poster[:5]:
            assert "poster_url" in m, f"poster_url missing on movie with poster_path: {m.get('title')}"
            assert m["poster_url"].startswith("https://image.tmdb.org/t/p/w185"), m["poster_url"]

    def test_popular_movies_no_duplicates(self, api_client):
        resp = api_client.get(f"{API}/onboarding/popular-movies", timeout=60)
        results = resp.json().get("results", [])
        ids = [m["id"] for m in results]
        assert len(ids) == len(set(ids)), "Duplicate movie IDs found in results"


# ---------- /api/onboarding/skip ----------
class TestSkipOnboarding:
    def test_skip_requires_auth(self, api_client):
        resp = api_client.post(f"{API}/onboarding/skip", json={"skipped": True})
        assert resp.status_code in (401, 403), f"got {resp.status_code}"

    def test_skip_persists(self, api_client, auth_headers):
        resp = api_client.post(
            f"{API}/onboarding/skip",
            headers=auth_headers,
            json={"skipped": True},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is True
        assert data.get("onboarding_skipped") is True

        # Verify state via eligibility endpoint
        elig = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()
        assert elig["onboarding_skipped"] is True

    def test_skip_does_not_change_eligibility_when_below_minimum(self, api_client, auth_headers):
        """Skipping should NOT prevent re-prompting if user is still below 5 movies."""
        elig_before = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()

        # Skip
        api_client.post(f"{API}/onboarding/skip", headers=auth_headers, json={"skipped": True})

        elig_after = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()

        # Eligibility should still be based on diary_count < 5 (skip does not block it)
        assert elig_after["eligible"] == (elig_after["diary_count"] < 5)
        assert elig_after["diary_count"] == elig_before["diary_count"]


# ---------- /api/onboarding/complete ----------
class TestCompleteOnboarding:
    def test_complete_requires_auth(self, api_client):
        resp = api_client.post(f"{API}/onboarding/complete", json={})
        assert resp.status_code in (401, 403), f"got {resp.status_code}"

    def test_complete_persists(self, api_client, auth_headers):
        resp = api_client.post(f"{API}/onboarding/complete", headers=auth_headers, json={})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is True
        assert data.get("onboarding_completed") is True

        # Verify state
        elig = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()
        assert elig["onboarding_completed"] is True


# ---------- End-to-end add movie flow ----------
class TestOnboardingAddMovieFlow:
    def test_add_movie_via_watch_history_updates_diary_count(self, api_client, auth_headers):
        """The onboarding UI calls POST /api/user/watch-history to add a movie.
        Verify the flow: fetch popular movies -> add one -> diary_count increases -> movies_needed decreases.
        """
        # Get initial eligibility
        elig_before = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()
        initial_diary_count = elig_before["diary_count"]
        initial_needed = elig_before["movies_needed"]

        # Get popular movies
        pop_resp = api_client.get(f"{API}/onboarding/popular-movies", timeout=60)
        assert pop_resp.status_code == 200
        movies = pop_resp.json().get("results", [])
        assert len(movies) > 0

        # Get existing diary to pick a movie not already added
        hist_resp = api_client.get(f"{API}/user/watch-history", headers=auth_headers)
        existing_ids = {m.get("tmdb_id") for m in (hist_resp.json() if hist_resp.status_code == 200 else [])}

        candidate = None
        for m in movies:
            if m["id"] not in existing_ids:
                candidate = m
                break
        assert candidate, "No candidate movie available to add"

        # Add the movie via watch-history endpoint (mimicking onboarding flow)
        add_resp = api_client.post(
            f"{API}/user/watch-history",
            headers=auth_headers,
            json={
                "tmdb_id": candidate["id"],
                "user_rating": 7.5,
                "watched_date": "2026-01-15",
                "title": candidate["title"],
                "poster_path": candidate.get("poster_path"),
                "comment": "",
            },
        )
        assert add_resp.status_code in (200, 201), f"add failed: {add_resp.status_code} {add_resp.text}"

        # Verify eligibility updated
        elig_after = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()
        assert elig_after["diary_count"] == initial_diary_count + 1, (
            f"diary_count did not increase: before={initial_diary_count}, after={elig_after['diary_count']}"
        )
        expected_needed = max(0, initial_needed - 1)
        assert elig_after["movies_needed"] == expected_needed

        # Cleanup: remove the movie we just added so tests remain idempotent
        try:
            api_client.delete(f"{API}/user/watch-history/{candidate['id']}", headers=auth_headers)
        except Exception:
            pass

    def test_onboarding_no_longer_eligible_after_5_movies(self, api_client, auth_headers):
        """This is a read-only check: if diary_count >= 5, eligible should be False."""
        elig = api_client.get(f"{API}/onboarding/eligibility", headers=auth_headers).json()
        if elig["diary_count"] >= 5:
            assert elig["eligible"] is False
            assert elig["movies_needed"] == 0
        else:
            assert elig["eligible"] is True
            assert elig["movies_needed"] > 0


# ---------- Home page sections load ----------
class TestHomeSections:
    """Verify home page auxiliary endpoints still work (regression)."""

    def test_trending_movies(self, api_client, auth_headers):
        resp = api_client.get(f"{API}/movies/trending", headers=auth_headers)
        # Some deployments use different endpoint names; accept 200 or 404 (skip if not present)
        if resp.status_code == 404:
            pytest.skip("/api/movies/trending not present")
        assert resp.status_code == 200, resp.text

    def test_user_profile(self, api_client, auth_headers):
        resp = api_client.get(f"{API}/user/profile", headers=auth_headers)
        if resp.status_code == 404:
            pytest.skip("/api/user/profile not present")
        assert resp.status_code == 200
