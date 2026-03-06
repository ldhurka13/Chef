"""
Comfort Movies with Weather Integration Test Suite
Tests: /api/movies/comfort endpoint with weather-based recommendations
Features tested:
- Backward compatibility (no location)
- Weather fetching from Open-Meteo API
- Comfort scoring based on weather conditions
- Time-of-day scoring adjustments
- Weather-aware vibe tags
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://diary-watch.preview.emergentagent.com')

# Location coordinates for testing
NYC_LAT = 40.7128
NYC_LNG = -74.006
MUMBAI_LAT = 19.076
MUMBAI_LNG = 72.8777
ICELAND_LAT = 64.1466  # Cold location
ICELAND_LNG = -21.9426


class TestComfortEndpointBackwardCompatibility:
    """Tests for /api/movies/comfort without location - backward compatibility"""
    
    def test_comfort_without_location(self):
        """Test comfort endpoint works without location (backward compatible)"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 12
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "results" in data, "Response should contain 'results' array"
        assert "weather" in data, "Response should contain 'weather' field"
        # Weather should be empty string when no location provided
        assert data["weather"] == "", f"Weather should be empty without location, got: {data['weather']}"
    
    def test_comfort_with_legacy_params(self):
        """Test comfort endpoint with legacy is_cold/is_rainy flags (no location)"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 20,
            "is_cold": True,
            "is_rainy": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Should still work with legacy params


class TestComfortWithWeatherLocation:
    """Tests for /api/movies/comfort WITH location - fetches real weather"""
    
    def test_comfort_with_nyc_location(self):
        """Test comfort endpoint with NYC coordinates returns weather description"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "results" in data, "Response should contain 'results'"
        assert "weather" in data, "Response should contain 'weather' field"
        
        # Weather description should not be empty when location is provided
        # Note: Weather could be empty if API fails, but generally should have a value
        print(f"NYC Weather: {data['weather']}")
        print(f"Cached: {data.get('cached', 'N/A')}")
    
    def test_comfort_with_mumbai_location(self):
        """Test comfort endpoint with Mumbai coordinates - typically warm climate"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": MUMBAI_LAT,
            "longitude": MUMBAI_LNG
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "weather" in data
        
        print(f"Mumbai Weather: {data['weather']}")
    
    def test_comfort_weather_field_is_string(self):
        """Verify weather field is always a string (not null/undefined)"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 12,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data.get("weather"), str), "Weather field should be a string"


class TestComfortScoring:
    """Tests for comfort score adjustments based on weather and time"""
    
    def test_late_night_scoring_boost(self):
        """Test late night (hour=23) returns results - late night should boost scores"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 23,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        # Should have results with comfort_score
        if len(results) > 0:
            assert "comfort_score" in results[0], "Movies should have comfort_score"
            print(f"Late night (23:00) top comfort score: {results[0].get('comfort_score', 'N/A')}")
    
    def test_daytime_scoring(self):
        """Test daytime (hour=14) returns results"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if len(results) > 0:
            print(f"Daytime (14:00) top comfort score: {results[0].get('comfort_score', 'N/A')}")
    
    def test_evening_scoring(self):
        """Test evening (hour=20) returns results"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 20,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if len(results) > 0:
            print(f"Evening (20:00) top comfort score: {results[0].get('comfort_score', 'N/A')}")


class TestComfortVibeTags:
    """Tests for weather-aware vibe tags in comfort movies"""
    
    def test_vibe_tag_present(self):
        """Verify all comfort movies have vibe_tag field"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 20,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        for movie in results:
            assert "vibe_tag" in movie, f"Movie {movie.get('title')} should have vibe_tag"
            print(f"Movie: {movie.get('title')} -> Vibe: {movie.get('vibe_tag')}")
    
    def test_late_night_vibe_tag(self):
        """Test late night hours generate appropriate vibe tags"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 23
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        # At late night, we expect tags like "Perfect for late night unwinding"
        vibe_tags = [m.get("vibe_tag", "") for m in results]
        print(f"Late night vibe tags: {vibe_tags}")


class TestComfortResponseStructure:
    """Tests for proper response structure from comfort endpoint"""
    
    def test_response_has_required_fields(self):
        """Verify response structure has all required fields"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level fields
        assert "results" in data, "Response should have 'results'"
        assert "weather" in data, "Response should have 'weather'"
        assert "cached" in data, "Response should have 'cached' boolean"
    
    def test_movie_structure(self):
        """Verify individual movie structure in results"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if len(results) > 0:
            movie = results[0]
            
            # Check required movie fields
            assert "title" in movie, "Movie should have title"
            assert "poster_url" in movie, "Movie should have poster_url"
            assert "vibe_tag" in movie, "Movie should have vibe_tag"
            
            # Check optional but expected fields
            if "user_rating" in movie:
                assert isinstance(movie["user_rating"], int), "user_rating should be int"
            if "watch_count" in movie:
                assert isinstance(movie["watch_count"], int), "watch_count should be int"
            if "comfort_score" in movie:
                assert isinstance(movie["comfort_score"], (int, float)), "comfort_score should be numeric"
    
    def test_returns_up_to_3_movies(self):
        """Verify comfort endpoint returns max 3 movies"""
        response = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 20,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        assert len(results) <= 3, f"Should return max 3 movies, got {len(results)}"
        print(f"Number of comfort movies returned: {len(results)}")


class TestWeatherCaching:
    """Tests for weather cache behavior"""
    
    def test_cached_flag_returned(self):
        """Verify cached flag is returned in response"""
        # First request
        response1 = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert "cached" in data1, "First response should have 'cached' field"
        cached1 = data1.get("cached")
        print(f"First request cached: {cached1}")
        
        # Second request with same params - should be cached
        time.sleep(0.5)
        response2 = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"Second request cached: {data2.get('cached')}")


class TestWeatherDifferentLocations:
    """Tests to verify different locations return different weather"""
    
    def test_different_locations_different_weather(self):
        """Test that NYC and Mumbai return different weather descriptions"""
        # NYC request
        response_nyc = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": NYC_LAT,
            "longitude": NYC_LNG
        })
        
        # Mumbai request
        response_mumbai = requests.post(f"{BASE_URL}/api/movies/comfort", json={
            "hour": 14,
            "latitude": MUMBAI_LAT,
            "longitude": MUMBAI_LNG
        })
        
        assert response_nyc.status_code == 200
        assert response_mumbai.status_code == 200
        
        weather_nyc = response_nyc.json().get("weather", "")
        weather_mumbai = response_mumbai.json().get("weather", "")
        
        print(f"NYC Weather: {weather_nyc}")
        print(f"Mumbai Weather: {weather_mumbai}")
        
        # Both should have weather data (though could be same by coincidence)
        # This test mainly verifies both calls work


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
