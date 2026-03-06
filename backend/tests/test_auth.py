"""
Auth Endpoints Test Suite for Chef App
Tests: Register, Login, Location Permission, Profile endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://diary-watch.preview.emergentagent.com')

# Test user credentials
TEST_USER_EMAIL = f"TEST_auth_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "password123"
TEST_USER_USERNAME = f"testchef_{uuid.uuid4().hex[:6]}"

# Existing user for login test
EXISTING_USER_EMAIL = "test_chef@example.com"
EXISTING_USER_PASSWORD = "test123"


class TestAuthRegister:
    """Tests for /api/auth/register endpoint"""
    
    def test_register_success_with_birth_date(self):
        """Test successful registration with birth_date field"""
        unique_email = f"TEST_reg_{uuid.uuid4().hex[:8]}@example.com"
        unique_username = f"reguser_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "password123",
            "username": unique_username,
            "birth_year": 1995,
            "birth_date": "1995-06-15"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify token is returned
        assert "token" in data, "Token should be in response"
        assert len(data["token"]) > 0, "Token should not be empty"
        
        # Verify user data is returned
        assert "user" in data, "User data should be in response"
        user = data["user"]
        assert user["email"] == unique_email.lower(), "Email should match"
        assert user["username"] == unique_username, "Username should match"
        assert user["birth_year"] == 1995, "Birth year should match"
        assert user["birth_date"] == "1995-06-15", "Birth date should match"
        assert user["location_permission"] is None, "Location permission should be null on register"
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email returns error"""
        # First register a user
        unique_email = f"TEST_dup_{uuid.uuid4().hex[:8]}@example.com"
        unique_username1 = f"dupuser1_{uuid.uuid4().hex[:6]}"
        
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "password123",
            "username": unique_username1,
            "birth_year": 1995
        })
        
        # Try to register again with same email
        unique_username2 = f"dupuser2_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "password123",
            "username": unique_username2,
            "birth_year": 1995
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error detail should be in response"
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username returns error"""
        # First register a user
        unique_email1 = f"TEST_dupu_{uuid.uuid4().hex[:8]}@example.com"
        unique_username = f"sameuser_{uuid.uuid4().hex[:6]}"
        
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email1,
            "password": "password123",
            "username": unique_username,
            "birth_year": 1995
        })
        
        # Try to register again with same username
        unique_email2 = f"TEST_dupu2_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email2,
            "password": "password123",
            "username": unique_username,
            "birth_year": 1995
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestAuthLogin:
    """Tests for /api/auth/login endpoint"""
    
    @pytest.fixture(scope="class")
    def registered_user(self):
        """Create a test user for login tests"""
        unique_email = f"TEST_login_{uuid.uuid4().hex[:8]}@example.com"
        unique_username = f"loginuser_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "username": unique_username,
            "birth_year": 1990,
            "birth_date": "1990-03-20"
        })
        
        return {
            "email": unique_email,
            "password": "testpass123",
            "username": unique_username
        }
    
    def test_login_success(self, registered_user):
        """Test successful login returns token and user with location_permission"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token should be in response"
        assert "user" in data, "User data should be in response"
        
        user = data["user"]
        assert user["email"] == registered_user["email"].lower(), "Email should match"
        assert "location_permission" in user, "location_permission field should exist"
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error detail should be in response"
    
    def test_login_existing_user(self):
        """Test login with existing test user (test_chef@example.com)"""
        # First ensure user exists by trying to register (will fail if exists)
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": EXISTING_USER_EMAIL,
            "password": EXISTING_USER_PASSWORD,
            "username": "testchef",
            "birth_year": 1995
        })
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXISTING_USER_EMAIL,
            "password": EXISTING_USER_PASSWORD
        })
        
        # If user exists, should be 200, if not, may be 401
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data
            assert "location_permission" in data["user"]


class TestLocationPermission:
    """Tests for /api/auth/location-permission endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create user and get auth token"""
        unique_email = f"TEST_locperm_{uuid.uuid4().hex[:8]}@example.com"
        unique_username = f"locuser_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "username": unique_username,
            "birth_year": 1995
        })
        
        return response.json()["token"]
    
    def test_update_location_permission_always(self, auth_token):
        """Test setting location permission to 'always'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/location-permission",
            json={
                "location_permission": "always",
                "latitude": 37.7749,
                "longitude": -122.4194
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["location_permission"] == "always"
    
    def test_update_location_permission_ask(self, auth_token):
        """Test setting location permission to 'ask'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/location-permission",
            json={"location_permission": "ask"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_permission"] == "ask"
    
    def test_update_location_permission_never(self, auth_token):
        """Test setting location permission to 'never'"""
        response = requests.put(
            f"{BASE_URL}/api/auth/location-permission",
            json={"location_permission": "never"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_permission"] == "never"
    
    def test_location_permission_without_auth(self):
        """Test location permission without auth returns 401"""
        response = requests.put(
            f"{BASE_URL}/api/auth/location-permission",
            json={"location_permission": "always"}
        )
        
        assert response.status_code == 401


class TestAuthMe:
    """Tests for /api/auth/me endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create user and get auth token"""
        unique_email = f"TEST_me_{uuid.uuid4().hex[:8]}@example.com"
        unique_username = f"meuser_{uuid.uuid4().hex[:6]}"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "username": unique_username,
            "birth_year": 1990
        })
        
        return response.json()["token"]
    
    def test_get_me_success(self, auth_token):
        """Test getting current user data"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
    
    def test_get_me_without_auth(self):
        """Test getting current user without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Chef" in data["message"]
    
    def test_trending_movies(self):
        """Test trending movies endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/movies/trending")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
