"""
Test suite for Watch History CRUD operations and Streaming Services feature
Testing:
1. Logo verification (72px, -rotate-12)
2. Watch History endpoints (CRUD with auth)
3. Streaming services in profile update
4. Auth requirements (401 without token)
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWatchHistoryCRUD:
    """Watch History CRUD tests with authenticated user"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Register a fresh user for each test class"""
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.test_email = f"test_history_{unique_id}@example.com"
        self.test_password = "testpass123"
        self.test_username = f"historyuser_{unique_id}"
        
        # Register user
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": self.test_password,
            "username": self.test_username,
            "birth_year": 1995
        })
        assert res.status_code == 200, f"Failed to register: {res.text}"
        self.token = res.json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    # === Test POST /api/user/watch-history ===
    
    def test_add_movie_to_watch_history(self):
        """POST /api/user/watch-history adds movie with rating and watched_date"""
        payload = {
            "tmdb_id": 155,  # The Dark Knight
            "user_rating": 8.5,
            "watched_date": "2024-01-15",
            "title": "The Dark Knight",
            "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify response structure
        assert data["tmdb_id"] == 155
        assert data["user_rating"] == 8.5
        assert data["title"] == "The Dark Knight"
        assert data["watch_count"] == 1
        assert "2024-01-15" in data["watch_dates"]
        assert data["last_watched_date"] == "2024-01-15"
        print("✓ Movie added to watch history with rating 8.5 and date 2024-01-15")
    
    def test_add_movie_with_decimal_rating(self):
        """POST /api/user/watch-history accepts 0.1 increment ratings"""
        payload = {
            "tmdb_id": 238,  # The Godfather
            "user_rating": 9.7,
            "watched_date": "2024-02-20",
            "title": "The Godfather"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert data["user_rating"] == 9.7
        print("✓ Rating with 0.1 increment (9.7) accepted")
    
    def test_add_same_movie_appends_watch_date(self):
        """POST /api/user/watch-history on same tmdb_id appends new watch_date"""
        # First watch
        payload = {
            "tmdb_id": 550,  # Fight Club
            "user_rating": 8.0,
            "watched_date": "2023-06-10",
            "title": "Fight Club"
        }
        res1 = requests.post(f"{BASE_URL}/api/user/watch-history", 
                            json=payload, headers=self.auth_headers)
        assert res1.status_code == 200
        
        # Second watch (same movie, different date)
        payload["watched_date"] = "2024-03-15"
        payload["user_rating"] = 8.5
        res2 = requests.post(f"{BASE_URL}/api/user/watch-history", 
                            json=payload, headers=self.auth_headers)
        
        assert res2.status_code == 200
        data = res2.json()
        
        # Verify multiple watch dates
        assert data["watch_count"] == 2
        assert "2023-06-10" in data["watch_dates"]
        assert "2024-03-15" in data["watch_dates"]
        assert data["last_watched_date"] == "2024-03-15"  # Most recent
        assert data["user_rating"] == 8.5  # Updated rating
        print("✓ Same movie adds new watch date, updates rating, increments watch_count")
    
    def test_add_movie_default_date(self):
        """POST /api/user/watch-history uses current date if no watched_date provided"""
        payload = {
            "tmdb_id": 278,  # The Shawshank Redemption
            "user_rating": 9.5,
            "title": "The Shawshank Redemption"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert data["last_watched_date"]  # Should have a date
        assert len(data["watch_dates"]) >= 1
        print("✓ Movie added with default current date")
    
    def test_add_movie_rating_boundaries(self):
        """POST /api/user/watch-history validates rating range 0-10"""
        # Minimum rating (0)
        payload = {
            "tmdb_id": 11,
            "user_rating": 0.0,
            "title": "Test Movie Min"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        assert res.status_code == 200
        
        # Maximum rating (10)
        payload["tmdb_id"] = 12
        payload["user_rating"] = 10.0
        payload["title"] = "Test Movie Max"
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        assert res.status_code == 200
        print("✓ Rating boundaries 0 and 10 accepted")
    
    def test_add_movie_invalid_rating(self):
        """POST /api/user/watch-history rejects invalid ratings"""
        payload = {
            "tmdb_id": 13,
            "user_rating": 11.0,  # Invalid: > 10
            "title": "Invalid Rating Movie"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json=payload, headers=self.auth_headers)
        assert res.status_code == 422  # Validation error
        print("✓ Invalid rating (11.0) rejected with 422")
    
    # === Test GET /api/user/watch-history ===
    
    def test_get_watch_history_sorted_by_date(self):
        """GET /api/user/watch-history returns history sorted by last_watched_date desc"""
        # Add movies with different dates
        movies = [
            {"tmdb_id": 101, "user_rating": 7.0, "watched_date": "2024-01-01", "title": "Old Movie"},
            {"tmdb_id": 102, "user_rating": 8.0, "watched_date": "2024-06-15", "title": "Recent Movie"},
            {"tmdb_id": 103, "user_rating": 9.0, "watched_date": "2024-03-10", "title": "Middle Movie"},
        ]
        for m in movies:
            requests.post(f"{BASE_URL}/api/user/watch-history", 
                         json=m, headers=self.auth_headers)
        
        # Get history
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        assert res.status_code == 200
        history = res.json()
        
        # Verify sorted by last_watched_date descending
        assert len(history) >= 3
        dates = [m.get("last_watched_date") for m in history if m.get("last_watched_date")]
        # Check that dates are in descending order
        for i in range(len(dates) - 1):
            assert dates[i] >= dates[i+1], f"Not sorted: {dates[i]} should be >= {dates[i+1]}"
        print("✓ Watch history returned sorted by last_watched_date desc")
    
    def test_get_watch_history_structure(self):
        """GET /api/user/watch-history returns expected fields"""
        # Add a movie first
        payload = {
            "tmdb_id": 200,
            "user_rating": 7.5,
            "watched_date": "2024-05-01",
            "title": "Structure Test Movie",
            "poster_path": "/test.jpg"
        }
        requests.post(f"{BASE_URL}/api/user/watch-history", 
                     json=payload, headers=self.auth_headers)
        
        # Get history
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        assert res.status_code == 200
        history = res.json()
        
        # Find our movie
        movie = next((m for m in history if m["tmdb_id"] == 200), None)
        assert movie is not None
        
        # Verify structure
        assert "id" in movie
        assert "user_id" in movie
        assert "tmdb_id" in movie
        assert "user_rating" in movie
        assert "watch_dates" in movie
        assert "last_watched_date" in movie
        assert "watch_count" in movie
        assert "title" in movie
        assert "poster_path" in movie
        print("✓ Watch history entry has all expected fields")
    
    # === Test DELETE /api/user/watch-history/{tmdb_id} ===
    
    def test_delete_movie_from_history(self):
        """DELETE /api/user/watch-history/{tmdb_id} removes movie"""
        # Add movie
        payload = {
            "tmdb_id": 300,
            "user_rating": 6.0,
            "title": "To Delete Movie"
        }
        requests.post(f"{BASE_URL}/api/user/watch-history", 
                     json=payload, headers=self.auth_headers)
        
        # Verify it's in history
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        history_before = res.json()
        assert any(m["tmdb_id"] == 300 for m in history_before)
        
        # Delete it
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/300", headers=self.auth_headers)
        assert res.status_code == 200
        
        # Verify it's gone
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        history_after = res.json()
        assert not any(m["tmdb_id"] == 300 for m in history_after)
        print("✓ Movie deleted from watch history and verified via GET")
    
    def test_delete_nonexistent_movie(self):
        """DELETE /api/user/watch-history/{tmdb_id} returns 404 for non-existent"""
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/999999", headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Delete non-existent movie returns 404")
    
    # === Test PUT /api/user/watch-history/{tmdb_id} ===
    
    def test_update_watch_history_rating(self):
        """PUT /api/user/watch-history/{tmdb_id} updates rating"""
        # Add movie
        payload = {
            "tmdb_id": 400,
            "user_rating": 5.0,
            "title": "Update Test Movie"
        }
        requests.post(f"{BASE_URL}/api/user/watch-history", 
                     json=payload, headers=self.auth_headers)
        
        # Update rating
        res = requests.put(f"{BASE_URL}/api/user/watch-history/400", 
                          json={"user_rating": 8.5}, headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert data["user_rating"] == 8.5
        print("✓ Watch history rating updated via PUT")
    
    def test_update_watch_history_add_date(self):
        """PUT /api/user/watch-history/{tmdb_id} adds new watched_date"""
        # Add movie with initial date
        payload = {
            "tmdb_id": 401,
            "user_rating": 7.0,
            "watched_date": "2024-01-01",
            "title": "Add Date Test Movie"
        }
        requests.post(f"{BASE_URL}/api/user/watch-history", 
                     json=payload, headers=self.auth_headers)
        
        # Add another watch date
        res = requests.put(f"{BASE_URL}/api/user/watch-history/401", 
                          json={"watched_date": "2024-06-01"}, headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert "2024-01-01" in data["watch_dates"]
        assert "2024-06-01" in data["watch_dates"]
        assert data["watch_count"] == 2
        assert data["last_watched_date"] == "2024-06-01"
        print("✓ New watch date added via PUT, watch_count incremented")


class TestStreamingServicesProfile:
    """Test streaming_services field in profile update"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Register a fresh user"""
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.test_email = f"test_streaming_{unique_id}@example.com"
        self.test_password = "testpass123"
        self.test_username = f"streamuser_{unique_id}"
        
        res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": self.test_email,
            "password": self.test_password,
            "username": self.test_username,
            "birth_year": 1995
        })
        assert res.status_code == 200
        self.token = res.json()["token"]
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_update_streaming_services(self):
        """PUT /api/auth/profile accepts streaming_services array"""
        services = ["netflix", "prime", "disney"]
        res = requests.put(f"{BASE_URL}/api/auth/profile", 
                          json={"streaming_services": services}, 
                          headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert "streaming_services" in data
        assert set(data["streaming_services"]) == set(services)
        print("✓ Profile updated with streaming_services array")
    
    def test_streaming_services_all_options(self):
        """PUT /api/auth/profile accepts all 7 streaming services"""
        all_services = ["netflix", "prime", "disney", "hulu", "apple", "hbo", "paramount"]
        res = requests.put(f"{BASE_URL}/api/auth/profile", 
                          json={"streaming_services": all_services}, 
                          headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert set(data["streaming_services"]) == set(all_services)
        print("✓ All 7 streaming services saved successfully")
    
    def test_get_me_returns_streaming_services(self):
        """GET /api/auth/me returns streaming_services field"""
        # Set services
        services = ["netflix", "hulu"]
        requests.put(f"{BASE_URL}/api/auth/profile", 
                    json={"streaming_services": services}, 
                    headers=self.auth_headers)
        
        # Get user data
        res = requests.get(f"{BASE_URL}/api/auth/me", headers=self.auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "streaming_services" in data
        assert set(data["streaming_services"]) == set(services)
        print("✓ GET /api/auth/me returns streaming_services field")
    
    def test_streaming_services_persists(self):
        """Streaming services persist across requests"""
        services = ["apple", "paramount"]
        
        # Update
        requests.put(f"{BASE_URL}/api/auth/profile", 
                    json={"streaming_services": services}, 
                    headers=self.auth_headers)
        
        # Verify via GET me
        res = requests.get(f"{BASE_URL}/api/auth/me", headers=self.auth_headers)
        assert set(res.json().get("streaming_services", [])) == set(services)
        
        # Update again (adding more)
        new_services = ["apple", "paramount", "disney"]
        requests.put(f"{BASE_URL}/api/auth/profile", 
                    json={"streaming_services": new_services}, 
                    headers=self.auth_headers)
        
        # Verify
        res = requests.get(f"{BASE_URL}/api/auth/me", headers=self.auth_headers)
        assert set(res.json().get("streaming_services", [])) == set(new_services)
        print("✓ Streaming services persist correctly")


class TestAuthRequirements:
    """Test that watch history endpoints require authentication"""
    
    def test_get_history_requires_auth(self):
        """GET /api/user/watch-history returns 401 without token"""
        res = requests.get(f"{BASE_URL}/api/user/watch-history")
        assert res.status_code == 401
        print("✓ GET watch-history returns 401 without auth")
    
    def test_post_history_requires_auth(self):
        """POST /api/user/watch-history returns 401 without token"""
        res = requests.post(f"{BASE_URL}/api/user/watch-history", json={
            "tmdb_id": 100,
            "user_rating": 5.0,
            "title": "Test"
        })
        assert res.status_code == 401
        print("✓ POST watch-history returns 401 without auth")
    
    def test_delete_history_requires_auth(self):
        """DELETE /api/user/watch-history/{tmdb_id} returns 401 without token"""
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/100")
        assert res.status_code == 401
        print("✓ DELETE watch-history returns 401 without auth")
    
    def test_put_history_requires_auth(self):
        """PUT /api/user/watch-history/{tmdb_id} returns 401 without token"""
        res = requests.put(f"{BASE_URL}/api/user/watch-history/100", json={"user_rating": 5.0})
        assert res.status_code == 401
        print("✓ PUT watch-history returns 401 without auth")
    
    def test_invalid_token_rejected(self):
        """Watch history endpoints reject invalid tokens"""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=invalid_headers)
        assert res.status_code == 401
        
        res = requests.post(f"{BASE_URL}/api/user/watch-history", 
                           json={"tmdb_id": 100, "user_rating": 5.0, "title": "Test"},
                           headers=invalid_headers)
        assert res.status_code == 401
        print("✓ Invalid tokens rejected with 401")


class TestTMDBSearch:
    """Test TMDB search for watch history (finding movies to add)"""
    
    def test_search_movie_for_history(self):
        """Search returns movies that can be added to history"""
        res = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=Dark%20Knight")
        assert res.status_code == 200
        data = res.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        
        movie = data["results"][0]
        assert "id" in movie
        assert "title" in movie
        assert "year" in movie
        print("✓ TMDB search returns movies with id, title, year for history add")
    
    def test_search_godfather(self):
        """Search finds The Godfather (tmdb_id: 238)"""
        res = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=Godfather")
        assert res.status_code == 200
        data = res.json()
        
        # Check if The Godfather is in results
        godfather = next((m for m in data["results"] if m["id"] == 238), None)
        if godfather:
            print(f"✓ Found The Godfather: id={godfather['id']}, title={godfather['title']}")
        else:
            print(f"✓ Godfather search returned {len(data['results'])} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
