"""
Test Profile Insights API - GET /api/user/profile-insights
Tests the auto-ranked read-only lists computed from watch history and ratings via TMDB API.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProfileInsights:
    """Profile insights endpoint tests - auto-ranked genres, actors, directors"""
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Use lbtest user which has 4 diary entries from Letterboxd import"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lbtest@example.com",
            "password": "test1234"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def empty_user_token(self):
        """Create a new user with no watch history"""
        timestamp = int(time.time())
        email = f"emptyinsights{timestamp}@test.com"
        username = f"emptyinsights{timestamp}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "test1234",
            "username": username
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        return response.json()["token"]
    
    def test_profile_insights_returns_200_for_authenticated_user(self, test_user_token):
        """GET /api/user/profile-insights returns 200 for authenticated user"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert "actors" in data
        assert "directors" in data
    
    def test_profile_insights_returns_401_without_auth(self):
        """GET /api/user/profile-insights returns 401 without authentication"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights")
        assert response.status_code == 401
    
    def test_profile_insights_genres_have_correct_fields(self, test_user_token):
        """Each genre item has name, score, count, avg_rating fields"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        genres = data.get("genres", [])
        assert len(genres) > 0, "Expected at least one genre from lbtest user"
        
        for genre in genres:
            assert "name" in genre, "Genre missing 'name' field"
            assert "score" in genre, "Genre missing 'score' field"
            assert "count" in genre, "Genre missing 'count' field"
            assert "avg_rating" in genre, "Genre missing 'avg_rating' field"
            assert isinstance(genre["name"], str)
            assert isinstance(genre["count"], int)
    
    def test_profile_insights_actors_have_correct_fields(self, test_user_token):
        """Each actor item has name, score, count, avg_rating, profile_path fields"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        actors = data.get("actors", [])
        assert len(actors) > 0, "Expected at least one actor from lbtest user"
        
        for actor in actors:
            assert "name" in actor, "Actor missing 'name' field"
            assert "score" in actor, "Actor missing 'score' field"
            assert "count" in actor, "Actor missing 'count' field"
            assert "avg_rating" in actor, "Actor missing 'avg_rating' field"
            assert "profile_path" in actor, "Actor missing 'profile_path' field"
    
    def test_profile_insights_directors_have_correct_fields(self, test_user_token):
        """Each director item has name, score, count, avg_rating, profile_path fields"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        directors = data.get("directors", [])
        assert len(directors) > 0, "Expected at least one director from lbtest user"
        
        for director in directors:
            assert "name" in director, "Director missing 'name' field"
            assert "score" in director, "Director missing 'score' field"
            assert "count" in director, "Director missing 'count' field"
            assert "avg_rating" in director, "Director missing 'avg_rating' field"
            assert "profile_path" in director, "Director missing 'profile_path' field"
    
    def test_profile_insights_actors_have_profile_images(self, test_user_token):
        """Actors should have profile_path from TMDB (at least some)"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        actors = response.json().get("actors", [])
        
        # At least one actor should have a profile image
        actors_with_images = [a for a in actors if a.get("profile_path")]
        assert len(actors_with_images) > 0, "Expected at least one actor with profile_path"
    
    def test_profile_insights_directors_have_profile_images(self, test_user_token):
        """Directors should have profile_path from TMDB (at least some)"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        directors = response.json().get("directors", [])
        
        # At least one director should have a profile image
        directors_with_images = [d for d in directors if d.get("profile_path")]
        assert len(directors_with_images) > 0, "Expected at least one director with profile_path"
    
    def test_profile_insights_returns_max_5_items(self, test_user_token):
        """Each category should return at most 5 items (top 5 ranking)"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert len(data.get("genres", [])) <= 5
        assert len(data.get("actors", [])) <= 5
        assert len(data.get("directors", [])) <= 5
    
    def test_profile_insights_empty_arrays_for_no_watch_history(self, empty_user_token):
        """Returns empty arrays when user has no watch history"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {empty_user_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("genres") == [], "Expected empty genres array"
        assert data.get("actors") == [], "Expected empty actors array"
        assert data.get("directors") == [], "Expected empty directors array"
    
    def test_profile_insights_genres_sorted_by_score(self, test_user_token):
        """Genres should be sorted by score (descending)"""
        response = requests.get(f"{BASE_URL}/api/user/profile-insights", headers={
            "Authorization": f"Bearer {test_user_token}"
        })
        assert response.status_code == 200
        genres = response.json().get("genres", [])
        
        if len(genres) >= 2:
            scores = [g["score"] for g in genres]
            assert scores == sorted(scores, reverse=True), "Genres not sorted by score descending"


class TestFavoriteMoviesProfile:
    """Tests for favorite_movies field in user profile (Top 5 Favorite Movies)"""
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Use lbtest user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lbtest@example.com",
            "password": "test1234"
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_profile_update_favorite_movies(self, test_user_token):
        """PUT /api/auth/profile accepts favorite_movies array"""
        test_movies = [
            {"id": 550, "title": "Fight Club", "year": "1999", "poster_url": None},
            {"id": 496243, "title": "Parasite", "year": "2019", "poster_url": None}
        ]
        
        response = requests.put(f"{BASE_URL}/api/auth/profile", 
            json={"favorite_movies": test_movies},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "favorite_movies" in data
        assert len(data["favorite_movies"]) == 2
        assert data["favorite_movies"][0]["id"] == 550
    
    def test_profile_favorite_movies_max_5(self, test_user_token):
        """favorite_movies should be limited to 5 items"""
        test_movies = [
            {"id": i, "title": f"Movie {i}", "year": "2020", "poster_url": None}
            for i in range(1, 7)  # 6 movies
        ]
        
        response = requests.put(f"{BASE_URL}/api/auth/profile", 
            json={"favorite_movies": test_movies},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Backend should limit to 5
        assert len(data["favorite_movies"]) <= 5
    
    def test_profile_favorite_movies_returned_on_login(self, test_user_token):
        """favorite_movies should be returned when user logs in"""
        # First set some movies
        test_movies = [{"id": 550, "title": "Fight Club", "year": "1999", "poster_url": None}]
        requests.put(f"{BASE_URL}/api/auth/profile", 
            json={"favorite_movies": test_movies},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # Then login again and check
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lbtest@example.com",
            "password": "test1234"
        })
        assert response.status_code == 200
        user = response.json()["user"]
        assert "favorite_movies" in user


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
