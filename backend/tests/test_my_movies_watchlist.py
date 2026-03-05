"""
Tests for My Movies Page features:
- Watchlist endpoints (POST/GET/DELETE /api/user/watchlist, GET /api/user/watchlist/check/{tmdb_id})
- Profile update with favorite_directors field
- Watch history endpoints (Diary tab uses these)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def test_user():
    """Create a unique test user for this module"""
    ts = str(int(time.time() * 1000))
    user_data = {
        "email": f"test_mymovies_{ts}@example.com",
        "password": "test1234",
        "username": f"testmymovies_{ts}",
        "birth_year": 1995
    }
    res = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    assert res.status_code == 200, f"Failed to create test user: {res.text}"
    data = res.json()
    return {
        "token": data["token"],
        "user": data["user"],
        "email": user_data["email"],
        "password": user_data["password"]
    }


class TestWatchlistEndpoints:
    """Tests for /api/user/watchlist endpoints"""
    
    def test_get_watchlist_empty(self, test_user):
        """GET /api/user/watchlist returns empty list initially"""
        res = requests.get(
            f"{BASE_URL}/api/user/watchlist",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 0
        print("PASS: GET /api/user/watchlist returns empty list for new user")
    
    def test_add_to_watchlist(self, test_user):
        """POST /api/user/watchlist adds movie correctly"""
        payload = {
            "tmdb_id": 550,  # Fight Club
            "title": "Fight Club",
            "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "genres": ["Drama", "Thriller"]
        }
        res = requests.post(
            f"{BASE_URL}/api/user/watchlist",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200, f"Failed to add to watchlist: {res.text}"
        data = res.json()
        assert data["tmdb_id"] == 550
        assert data["title"] == "Fight Club"
        assert data["poster_path"] == "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"
        assert data["release_date"] == "1999-10-15"
        assert data["vote_average"] == 8.4
        assert data["genres"] == ["Drama", "Thriller"]
        assert "added_at" in data
        assert "id" in data
        print("PASS: POST /api/user/watchlist adds movie with all fields")
    
    def test_add_duplicate_to_watchlist(self, test_user):
        """POST /api/user/watchlist rejects duplicate"""
        payload = {
            "tmdb_id": 550,  # Fight Club - already added
            "title": "Fight Club",
        }
        res = requests.post(
            f"{BASE_URL}/api/user/watchlist",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 400
        assert "Already in watchlist" in res.json().get("detail", "")
        print("PASS: POST /api/user/watchlist rejects duplicate movie")
    
    def test_get_watchlist_with_items(self, test_user):
        """GET /api/user/watchlist returns added items"""
        res = requests.get(
            f"{BASE_URL}/api/user/watchlist",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert any(item["tmdb_id"] == 550 for item in data)
        print("PASS: GET /api/user/watchlist returns added movies")
    
    def test_check_watchlist_in_list(self, test_user):
        """GET /api/user/watchlist/check/{tmdb_id} returns true for movie in watchlist"""
        res = requests.get(
            f"{BASE_URL}/api/user/watchlist/check/550",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        assert res.json()["in_watchlist"] == True
        print("PASS: GET /api/user/watchlist/check/{id} returns true for movie in list")
    
    def test_check_watchlist_not_in_list(self, test_user):
        """GET /api/user/watchlist/check/{tmdb_id} returns false for movie not in watchlist"""
        res = requests.get(
            f"{BASE_URL}/api/user/watchlist/check/9999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        assert res.json()["in_watchlist"] == False
        print("PASS: GET /api/user/watchlist/check/{id} returns false for movie not in list")
    
    def test_delete_from_watchlist(self, test_user):
        """DELETE /api/user/watchlist/{tmdb_id} removes movie"""
        res = requests.delete(
            f"{BASE_URL}/api/user/watchlist/550",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        assert "Removed from watchlist" in res.json().get("message", "")
        print("PASS: DELETE /api/user/watchlist/{id} removes movie")
        
        # Verify it's removed
        check_res = requests.get(
            f"{BASE_URL}/api/user/watchlist/check/550",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert check_res.json()["in_watchlist"] == False
        print("PASS: Movie verified removed from watchlist after delete")
    
    def test_delete_not_in_watchlist(self, test_user):
        """DELETE /api/user/watchlist/{tmdb_id} returns 404 for movie not in list"""
        res = requests.delete(
            f"{BASE_URL}/api/user/watchlist/9999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 404
        print("PASS: DELETE /api/user/watchlist/{id} returns 404 for non-existent movie")
    
    def test_watchlist_requires_auth(self):
        """Watchlist endpoints require authentication"""
        # GET watchlist
        res = requests.get(f"{BASE_URL}/api/user/watchlist")
        assert res.status_code == 401
        
        # POST watchlist
        res = requests.post(f"{BASE_URL}/api/user/watchlist", json={"tmdb_id": 123})
        assert res.status_code == 401
        
        # DELETE watchlist
        res = requests.delete(f"{BASE_URL}/api/user/watchlist/123")
        assert res.status_code == 401
        
        print("PASS: All watchlist endpoints require authentication")


class TestProfileFavoriteDirectors:
    """Tests for favorite_directors field in profile update"""
    
    def test_update_profile_favorite_directors(self, test_user):
        """PUT /api/auth/profile accepts favorite_directors field"""
        payload = {
            "favorite_directors": ["Christopher Nolan", "David Fincher", "Quentin Tarantino"]
        }
        res = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "favorite_directors" in data
        assert data["favorite_directors"] == ["Christopher Nolan", "David Fincher", "Quentin Tarantino"]
        print("PASS: PUT /api/auth/profile accepts favorite_directors field")
    
    def test_get_profile_has_favorite_directors(self, test_user):
        """GET /api/auth/me returns favorite_directors"""
        res = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "favorite_directors" in data
        assert len(data["favorite_directors"]) == 3
        print("PASS: GET /api/auth/me returns favorite_directors in profile")
    
    def test_favorite_directors_limit(self, test_user):
        """PUT /api/auth/profile limits favorite_directors to 20"""
        directors = [f"Director {i}" for i in range(25)]
        payload = {"favorite_directors": directors}
        res = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        # Should be limited to 20
        assert len(data["favorite_directors"]) <= 20
        print("PASS: favorite_directors field limited to max 20 entries")


class TestWatchHistoryDiary:
    """Tests for watch history (Diary tab uses these endpoints)"""
    
    def test_add_to_diary(self, test_user):
        """POST /api/user/watch-history adds movie to diary"""
        payload = {
            "tmdb_id": 680,  # Pulp Fiction
            "user_rating": 9.0,
            "watched_date": "2025-01-15",
            "title": "Pulp Fiction",
            "poster_path": "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg"
        }
        res = requests.post(
            f"{BASE_URL}/api/user/watch-history",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["tmdb_id"] == 680
        assert data["user_rating"] == 9.0
        assert data["title"] == "Pulp Fiction"
        assert "2025-01-15" in data.get("watch_dates", [])
        print("PASS: POST /api/user/watch-history adds movie to diary")
    
    def test_get_diary(self, test_user):
        """GET /api/user/watch-history returns diary entries"""
        res = requests.get(
            f"{BASE_URL}/api/user/watch-history",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert any(item["tmdb_id"] == 680 for item in data)
        print("PASS: GET /api/user/watch-history returns diary entries")
    
    def test_remove_from_diary(self, test_user):
        """DELETE /api/user/watch-history/{tmdb_id} removes from diary"""
        res = requests.delete(
            f"{BASE_URL}/api/user/watch-history/680",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        
        # Verify removal
        get_res = requests.get(
            f"{BASE_URL}/api/user/watch-history",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert not any(item["tmdb_id"] == 680 for item in get_res.json())
        print("PASS: DELETE /api/user/watch-history/{id} removes from diary")


class TestGenresEndpoint:
    """Test /api/genres endpoint for Profile tab"""
    
    def test_get_genres(self):
        """GET /api/genres returns list of genres"""
        res = requests.get(f"{BASE_URL}/api/genres")
        assert res.status_code == 200
        data = res.json()
        assert "genres" in data
        assert len(data["genres"]) > 0
        # Check structure
        genre = data["genres"][0]
        assert "id" in genre
        assert "name" in genre
        print("PASS: GET /api/genres returns list of genres with id and name")


class TestProfileFavoriteGenres:
    """Tests for favorite_genres field in profile"""
    
    def test_update_favorite_genres(self, test_user):
        """PUT /api/auth/profile accepts favorite_genres field"""
        payload = {
            "favorite_genres": ["Action", "Drama", "Thriller"]
        }
        res = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert "favorite_genres" in data
        assert data["favorite_genres"] == ["Action", "Drama", "Thriller"]
        print("PASS: PUT /api/auth/profile accepts favorite_genres field")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
