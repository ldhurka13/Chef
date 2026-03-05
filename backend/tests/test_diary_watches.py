"""
Test suite for Diary Watch Entry CRUD operations
Tests the enhanced diary feature with multiple watches per movie:
1. POST /api/user/watch-history/{tmdb_id}/watches - Add a new watch entry
2. PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} - Edit a watch entry
3. DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id} - Delete a watch entry
4. GET /api/user/watch-history - Verify watches array in response with auto-migration
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDiaryWatchEntries:
    """Test individual watch entry CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Register a fresh user for each test class"""
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.test_email = f"test_diary_watches_{unique_id}@example.com"
        self.test_password = "test1234"
        self.test_username = f"diarytest_{unique_id}"
        
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
        
        # Add a movie to diary first (required for watch entry operations)
        add_res = requests.post(f"{BASE_URL}/api/user/watch-history", json={
            "tmdb_id": 155,  # The Dark Knight
            "user_rating": 8.0,
            "watched_date": "2024-01-15",
            "title": "The Dark Knight",
            "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
        }, headers=self.auth_headers)
        assert add_res.status_code == 200, f"Failed to add movie: {add_res.text}"
        self.test_movie = add_res.json()
        self.test_tmdb_id = 155
        yield
    
    # === Test POST /api/user/watch-history/{tmdb_id}/watches ===
    
    def test_add_watch_entry_creates_new_watch(self):
        """POST /api/user/watch-history/{tmdb_id}/watches adds a new watch entry"""
        payload = {
            "rating": 9.0,
            "date": "2024-06-20",
            "comment": "Second viewing - noticed more details"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json=payload, headers=self.auth_headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify watches array exists and has 2 entries (initial + new)
        assert "watches" in data, "Response should contain watches array"
        assert len(data["watches"]) == 2, f"Expected 2 watches, got {len(data['watches'])}"
        
        # Verify watch_count updated
        assert data["watch_count"] == 2
        
        # Verify summary fields updated
        assert data["last_watched_date"] == "2024-06-20"  # Latest date
        assert data["user_rating"] == 9.0  # Latest rating
        print("✓ New watch entry added successfully with rating 9.0")
    
    def test_add_watch_entry_with_decimal_rating(self):
        """POST /api/user/watch-history/{tmdb_id}/watches accepts 0.1 increment ratings"""
        payload = {
            "rating": 8.7,
            "date": "2024-07-15",
            "comment": "Great rewatch"
        }
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json=payload, headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        # Find the new watch entry
        new_watch = [w for w in data["watches"] if w["date"] == "2024-07-15"]
        assert len(new_watch) == 1
        assert new_watch[0]["rating"] == 8.7
        print("✓ Rating with 0.1 increment (8.7) accepted")
    
    def test_add_watch_entry_rating_boundaries(self):
        """POST /api/user/watch-history/{tmdb_id}/watches validates rating 0-10"""
        # Test rating 0
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json={"rating": 0.0, "date": "2024-08-01"},
                           headers=self.auth_headers)
        assert res.status_code == 200, "Rating 0 should be accepted"
        
        # Test rating 10
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json={"rating": 10.0, "date": "2024-08-02"},
                           headers=self.auth_headers)
        assert res.status_code == 200, "Rating 10 should be accepted"
        print("✓ Rating boundaries 0 and 10 accepted")
    
    def test_add_watch_entry_invalid_rating(self):
        """POST /api/user/watch-history/{tmdb_id}/watches rejects rating > 10"""
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json={"rating": 11.0, "date": "2024-08-03"},
                           headers=self.auth_headers)
        assert res.status_code == 422, f"Expected 422 for invalid rating, got {res.status_code}"
        print("✓ Invalid rating (11.0) rejected with 422")
    
    def test_add_watch_entry_default_date(self):
        """POST /api/user/watch-history/{tmdb_id}/watches uses current date if not provided"""
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json={"rating": 7.5},
                           headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        # All watches should have a date
        for w in data["watches"]:
            assert w.get("date"), f"Watch entry missing date: {w}"
        print("✓ Watch entry added with default current date")
    
    def test_add_watch_entry_movie_not_in_history(self):
        """POST /api/user/watch-history/{tmdb_id}/watches returns 404 if movie not in history"""
        res = requests.post(f"{BASE_URL}/api/user/watch-history/999999/watches",
                           json={"rating": 8.0, "date": "2024-08-04"},
                           headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Add watch to non-existent movie returns 404")
    
    def test_add_watch_entry_comment_truncated(self):
        """POST /api/user/watch-history/{tmdb_id}/watches truncates comment to 500 chars"""
        long_comment = "x" * 600
        res = requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                           json={"rating": 7.0, "date": "2024-08-05", "comment": long_comment},
                           headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        # Find the new watch
        new_watch = [w for w in data["watches"] if w["date"] == "2024-08-05"]
        assert len(new_watch) == 1
        assert len(new_watch[0]["comment"]) <= 500
        print("✓ Long comment truncated to 500 characters")
    
    # === Test PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} ===
    
    def test_update_watch_entry_rating(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} updates rating"""
        # Get the initial watch entry ID
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        watch_id = movie["watches"][0]["id"]
        
        # Update rating
        res = requests.put(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/{watch_id}",
                          json={"rating": 9.5},
                          headers=self.auth_headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Find updated watch
        updated_watch = [w for w in data["watches"] if w["id"] == watch_id][0]
        assert updated_watch["rating"] == 9.5
        print("✓ Watch entry rating updated to 9.5")
    
    def test_update_watch_entry_date(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} updates date"""
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        watch_id = movie["watches"][0]["id"]
        
        res = requests.put(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/{watch_id}",
                          json={"date": "2024-09-15"},
                          headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        updated_watch = [w for w in data["watches"] if w["id"] == watch_id][0]
        assert updated_watch["date"] == "2024-09-15"
        print("✓ Watch entry date updated")
    
    def test_update_watch_entry_comment(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} updates comment"""
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        watch_id = movie["watches"][0]["id"]
        
        res = requests.put(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/{watch_id}",
                          json={"comment": "Updated comment - great movie!"},
                          headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        updated_watch = [w for w in data["watches"] if w["id"] == watch_id][0]
        assert updated_watch["comment"] == "Updated comment - great movie!"
        print("✓ Watch entry comment updated")
    
    def test_update_watch_entry_all_fields(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} updates all fields"""
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        watch_id = movie["watches"][0]["id"]
        
        res = requests.put(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/{watch_id}",
                          json={
                              "rating": 8.8,
                              "date": "2024-10-20",
                              "comment": "All fields updated"
                          },
                          headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        updated_watch = [w for w in data["watches"] if w["id"] == watch_id][0]
        assert updated_watch["rating"] == 8.8
        assert updated_watch["date"] == "2024-10-20"
        assert updated_watch["comment"] == "All fields updated"
        print("✓ All watch entry fields updated successfully")
    
    def test_update_watch_entry_not_found(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 404 for invalid watch_id"""
        res = requests.put(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/invalid-id",
                          json={"rating": 8.0},
                          headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Update non-existent watch entry returns 404")
    
    def test_update_watch_entry_movie_not_found(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 404 for invalid movie"""
        res = requests.put(f"{BASE_URL}/api/user/watch-history/999999/watches/some-id",
                          json={"rating": 8.0},
                          headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Update watch on non-existent movie returns 404")
    
    # === Test DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id} ===
    
    def test_delete_watch_entry_keeps_movie(self):
        """DELETE watch entry when movie has multiple watches keeps movie in history"""
        # First add another watch entry
        requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                     json={"rating": 8.5, "date": "2024-11-01"},
                     headers=self.auth_headers)
        
        # Get current state
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        initial_count = len(movie["watches"])
        assert initial_count >= 2, "Should have at least 2 watches"
        
        # Delete one watch entry
        watch_to_delete = movie["watches"][0]["id"]
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/{watch_to_delete}",
                             headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        
        # Movie should still exist with fewer watches
        assert "watches" in data
        assert len(data["watches"]) == initial_count - 1
        assert data.get("removed") != True  # Movie not removed
        print("✓ Watch entry deleted, movie kept in history with remaining watches")
    
    def test_delete_last_watch_removes_movie(self):
        """DELETE last watch entry removes movie from history entirely"""
        # Add a new movie with just one watch
        new_movie_res = requests.post(f"{BASE_URL}/api/user/watch-history", json={
            "tmdb_id": 238,  # The Godfather
            "user_rating": 9.0,
            "watched_date": "2024-11-10",
            "title": "The Godfather"
        }, headers=self.auth_headers)
        assert new_movie_res.status_code == 200
        new_movie = new_movie_res.json()
        
        # Get the watch ID
        watch_id = new_movie["watches"][0]["id"]
        
        # Delete the only watch
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/238/watches/{watch_id}",
                             headers=self.auth_headers)
        
        assert res.status_code == 200
        data = res.json()
        assert data.get("removed") == True, "Movie should be marked as removed"
        
        # Verify movie is no longer in history
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        godfather = [m for m in history_res.json() if m["tmdb_id"] == 238]
        assert len(godfather) == 0, "Movie should be removed from history"
        print("✓ Last watch deleted, movie removed from history entirely")
    
    def test_delete_watch_entry_not_found(self):
        """DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 404 for invalid watch"""
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches/invalid-id",
                             headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Delete non-existent watch entry returns 404")
    
    def test_delete_watch_entry_movie_not_found(self):
        """DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 404 for invalid movie"""
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/999999/watches/some-id",
                             headers=self.auth_headers)
        assert res.status_code == 404
        print("✓ Delete watch on non-existent movie returns 404")
    
    # === Test GET /api/user/watch-history watches array ===
    
    def test_get_watch_history_contains_watches_array(self):
        """GET /api/user/watch-history returns watches array for each movie"""
        res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        assert res.status_code == 200
        
        history = res.json()
        assert len(history) > 0
        
        for movie in history:
            assert "watches" in movie, f"Movie {movie.get('tmdb_id')} missing watches array"
            assert isinstance(movie["watches"], list)
            
            for watch in movie["watches"]:
                assert "id" in watch, "Watch missing id"
                assert "rating" in watch, "Watch missing rating"
                assert "date" in watch, "Watch missing date"
        
        print("✓ Watch history contains watches array with id, rating, date for each entry")
    
    def test_summary_fields_sync_with_watches(self):
        """Summary fields (user_rating, last_watched_date, watch_count) sync with watches"""
        # Add multiple watches
        dates_ratings = [
            ("2024-01-01", 7.0),
            ("2024-06-15", 8.5),
            ("2024-03-10", 7.5),
        ]
        for date, rating in dates_ratings[1:]:  # Skip first, already added in setup
            requests.post(f"{BASE_URL}/api/user/watch-history/{self.test_tmdb_id}/watches",
                         json={"rating": rating, "date": date},
                         headers=self.auth_headers)
        
        # Get history
        history_res = requests.get(f"{BASE_URL}/api/user/watch-history", headers=self.auth_headers)
        movie = [m for m in history_res.json() if m["tmdb_id"] == self.test_tmdb_id][0]
        
        # Verify summary matches watches
        assert movie["watch_count"] == len(movie["watches"])
        
        # Last watched should be the most recent date
        watch_dates = sorted([w["date"] for w in movie["watches"]], reverse=True)
        assert movie["last_watched_date"] == watch_dates[0]
        
        # User rating should be from the most recent watch
        latest_watch = max(movie["watches"], key=lambda w: w["date"])
        assert movie["user_rating"] == latest_watch["rating"]
        
        print("✓ Summary fields correctly sync with watches array")


class TestDiaryAuthRequirements:
    """Test that watch entry endpoints require authentication"""
    
    def test_add_watch_entry_requires_auth(self):
        """POST /api/user/watch-history/{tmdb_id}/watches returns 401 without token"""
        res = requests.post(f"{BASE_URL}/api/user/watch-history/155/watches",
                           json={"rating": 8.0})
        assert res.status_code == 401
        print("✓ Add watch entry returns 401 without auth")
    
    def test_update_watch_entry_requires_auth(self):
        """PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 401 without token"""
        res = requests.put(f"{BASE_URL}/api/user/watch-history/155/watches/some-id",
                          json={"rating": 8.0})
        assert res.status_code == 401
        print("✓ Update watch entry returns 401 without auth")
    
    def test_delete_watch_entry_requires_auth(self):
        """DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id} returns 401 without token"""
        res = requests.delete(f"{BASE_URL}/api/user/watch-history/155/watches/some-id")
        assert res.status_code == 401
        print("✓ Delete watch entry returns 401 without auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
