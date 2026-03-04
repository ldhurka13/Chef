"""
Test suite for User Details feature - iteration 6
Tests: Profile updates (gender, bio, actors, movies), avatar upload, 
TMDB movie search, Letterboxd CSV import/export
"""
import pytest
import requests
import os
import io
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Global test token and user - created once per session
_test_token = None
_test_user = None

def get_test_token():
    """Get or create test token for the session"""
    global _test_token, _test_user
    if _test_token is None:
        # Register a unique test user
        unique_id = f"test_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"{unique_id}@test.com",
            "password": "test123",
            "username": unique_id,
            "birth_year": 1995
        })
        if response.status_code == 200:
            _test_token = response.json()["token"]
            _test_user = response.json()["user"]
        else:
            raise Exception(f"Failed to create test user: {response.text}")
    return _test_token

class TestTMDBMovieSearch:
    """TMDB movie search endpoint tests (no auth required)"""
    
    def test_search_tmdb_basic(self):
        """Search TMDB for movies returns results"""
        response = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=godfather")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        
    def test_search_tmdb_result_structure(self):
        """TMDB results have required fields: id, title, year, poster_url, rating"""
        response = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=godfather")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        
        movie = data["results"][0]
        assert "id" in movie
        assert "title" in movie
        assert "year" in movie
        assert "poster_url" in movie
        assert "rating" in movie
        
    def test_search_tmdb_empty_query(self):
        """Empty query returns empty results"""
        response = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        
    def test_search_tmdb_short_query(self):
        """Query less than 2 chars returns empty results"""
        response = requests.get(f"{BASE_URL}/api/movies/search-tmdb?query=a")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []


class TestUserDetailsAuth:
    """User details endpoint tests with authentication"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token from shared session"""
        return get_test_token()
    
    def test_profile_update_gender(self, auth_token):
        """Update gender field persists correctly"""
        # Update gender
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"gender": "male"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("gender") == "male"
        
        # Verify persistence with GET /me
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json().get("gender") == "male"
        
        # Reset to original
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"gender": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_bio(self, auth_token):
        """Update bio field with character limit"""
        test_bio = "Cinephile, night owl, Kubrick devotee..."
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"bio": test_bio},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("bio") == test_bio
        
        # Test 150 char limit
        long_bio = "x" * 200
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"bio": long_bio},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("bio", "")) <= 150
        
        # Reset
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"bio": ""},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_favorite_actors(self, auth_token):
        """Update favorite actors list"""
        test_actors = ["Robert De Niro", "Al Pacino", "Leonardo DiCaprio"]
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_actors": test_actors},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("favorite_actors") == test_actors
        
        # Verify persistence
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json().get("favorite_actors") == test_actors
        
        # Reset
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_actors": []},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_favorite_actors_limit(self, auth_token):
        """Favorite actors limited to 20"""
        too_many_actors = [f"Actor {i}" for i in range(25)]
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_actors": too_many_actors},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("favorite_actors", [])) <= 20
        
        # Reset
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_actors": []},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_favorite_movies(self, auth_token):
        """Update favorite movies list with movie objects"""
        test_movies = [
            {"id": 238, "title": "The Godfather", "year": "1972", "poster_url": "https://image.tmdb.org/t/p/w185/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", "rating": 8.7},
            {"id": 240, "title": "The Godfather Part II", "year": "1974", "poster_url": "https://image.tmdb.org/t/p/w185/hek3koDUyRQk7FIhPXsa6mT2Zc3.jpg", "rating": 8.6}
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_movies": test_movies},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("favorite_movies", [])) == 2
        assert data["favorite_movies"][0]["id"] == 238
        
        # Reset
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_movies": []},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_favorite_movies_limit(self, auth_token):
        """Favorite movies limited to 5"""
        too_many_movies = [
            {"id": i, "title": f"Movie {i}", "year": "2020"}
            for i in range(10)
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_movies": too_many_movies},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("favorite_movies", [])) <= 5
        
        # Reset
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"favorite_movies": []},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
    def test_profile_update_all_fields(self, auth_token):
        """Update all user details fields at once"""
        update_data = {
            "gender": "non-binary",
            "bio": "Test bio for all fields update",
            "favorite_actors": ["Actor A", "Actor B"],
            "favorite_movies": [{"id": 155, "title": "The Dark Knight", "year": "2008"}]
        }
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("gender") == "non-binary"
        assert data.get("bio") == "Test bio for all fields update"
        assert len(data.get("favorite_actors", [])) == 2
        assert len(data.get("favorite_movies", [])) == 1
        
        # Reset all
        requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"gender": "", "bio": "", "favorite_actors": [], "favorite_movies": []},
            headers={"Authorization": f"Bearer {auth_token}"}
        )


class TestAvatarUpload:
    """Avatar upload endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token from shared session"""
        return get_test_token()
    
    def test_avatar_upload_jpeg(self, auth_token):
        """Upload JPEG avatar image"""
        # Create a minimal valid JPEG image
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x00, 0x31, 0xC4, 0x1F, 0xFF,
            0xD9
        ])
        
        files = {
            'file': ('test_avatar.jpg', io.BytesIO(jpeg_bytes), 'image/jpeg')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/upload-avatar",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert data["avatar_url"].startswith("/api/uploads/avatars/")
        
    def test_avatar_upload_invalid_type(self, auth_token):
        """Reject non-image files"""
        files = {
            'file': ('test.txt', io.BytesIO(b'not an image'), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/upload-avatar",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        
    def test_avatar_upload_requires_auth(self):
        """Avatar upload requires authentication"""
        files = {
            'file': ('test.jpg', io.BytesIO(b'\xFF\xD8\xFF'), 'image/jpeg')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/upload-avatar",
            files=files
        )
        
        assert response.status_code == 401


class TestLetterboxdImport:
    """Letterboxd CSV import/export tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token from shared session"""
        return get_test_token()
    
    def test_letterboxd_import_basic_csv(self, auth_token):
        """Import basic Letterboxd CSV format"""
        csv_content = """Title,Year,Rating
The Godfather,1972,5
The Dark Knight,2008,4.5
Inception,2010,4
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 3
        assert "message" in data
        
    def test_letterboxd_import_full_format(self, auth_token):
        """Import full Letterboxd export format with all columns"""
        csv_content = """Title,Year,Rating,Rating10,WatchedDate,tmdbID,imdbID,Rewatch,Tags,Review
The Godfather,1972,5,10,2024-01-15,238,tt0068646,false,"crime, classic",Great movie
Inception,2010,4,8,2024-02-20,27205,tt1375666,true,sci-fi,Mind-bending
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["rated"] == 2
        
    def test_letterboxd_import_name_column(self, auth_token):
        """Import CSV with Name column instead of Title"""
        csv_content = """Name,Year,Rating
The Matrix,1999,4.5
Fight Club,1999,4
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        
    def test_letterboxd_import_invalid_format(self, auth_token):
        """Reject non-CSV files"""
        files = {
            'file': ('data.txt', io.BytesIO(b'not a csv'), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        
    def test_letterboxd_import_empty_csv(self, auth_token):
        """Reject empty CSV files"""
        csv_content = """Title,Year,Rating
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400
        
    def test_letterboxd_data_retrieval(self, auth_token):
        """Get imported Letterboxd data"""
        # First import some data
        csv_content = """Title,Year,Rating
Test Movie,2020,4
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Now get the data
        response = requests.get(
            f"{BASE_URL}/api/auth/letterboxd-data",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("connected") == True
        assert "total_movies" in data
        assert "entries" in data
        
    def test_letterboxd_data_requires_auth(self):
        """Letterboxd data requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/letterboxd-data")
        assert response.status_code == 401
        
    def test_letterboxd_import_requires_auth(self):
        """Letterboxd import requires authentication"""
        csv_content = """Title,Year,Rating
Movie,2020,4
"""
        files = {
            'file': ('letterboxd.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/import-letterboxd",
            files=files
        )
        
        assert response.status_code == 401


class TestUserDetailsNoAuth:
    """Test endpoints that require auth return 401 without token"""
    
    def test_profile_update_requires_auth(self):
        """Profile update requires authentication"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"gender": "male"}
        )
        assert response.status_code == 401
        
    def test_get_me_requires_auth(self):
        """GET /me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
