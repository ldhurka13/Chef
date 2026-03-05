"""
Streaming Availability API Tests
Tests the Movies of the Night (RapidAPI) streaming integration with MongoDB caching.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://watchlist-diary.preview.emergentagent.com').rstrip('/')

# Test movie IDs with known streaming availability
DARK_KNIGHT_ID = 155  # Has Max, Hulu, Prime in US
GODFATHER_ID = 238    # Has Paramount+, Hulu in US
INVALID_MOVIE_ID = 9999999

# Allowed services as defined in backend
ALLOWED_SERVICES = {"netflix", "prime", "disney", "hulu", "apple", "hbo", "paramount"}

class TestStreamingAvailability:
    """Tests for GET /api/movies/{movie_id}/streaming endpoint"""
    
    def test_streaming_dark_knight_us(self):
        """Test streaming options for The Dark Knight in US returns expected structure"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        # Response structure validation
        assert "results" in data
        assert "country" in data
        assert "cached" in data
        assert data["country"] == "us"
        assert isinstance(data["results"], list)
        print(f"The Dark Knight streaming options: {len(data['results'])} found, cached={data['cached']}")
    
    def test_streaming_godfather_us(self):
        """Test streaming options for The Godfather in US"""
        response = requests.get(f"{BASE_URL}/api/movies/{GODFATHER_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert data["country"] == "us"
        print(f"The Godfather streaming options: {len(data['results'])} found")
    
    def test_streaming_option_fields(self):
        """Test that streaming options have required fields: service_name, type, link"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["results"]:
            for opt in data["results"]:
                # Required fields
                assert "service_id" in opt
                assert "service_name" in opt
                assert "service_color" in opt
                assert "type" in opt
                assert "link" in opt
                
                # Service must be in allowed list
                assert opt["service_id"] in ALLOWED_SERVICES, f"Unexpected service: {opt['service_id']}"
                
                # Type must be valid
                assert opt["type"] in ["subscription", "free", "addon", "rent", "buy"]
                
                # Link must be a URL
                assert opt["link"].startswith("http")
                
                print(f"  - {opt['service_name']}: {opt['type']}")
    
    def test_streaming_price_fields(self):
        """Test that rent/buy options have price fields"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        rent_or_buy_options = [opt for opt in data["results"] if opt["type"] in ["rent", "buy"]]
        
        for opt in rent_or_buy_options:
            assert "price" in opt, f"Missing price for {opt['type']} option"
            print(f"  - {opt['service_name']} {opt['type']}: {opt.get('price', 'N/A')}")
    
    def test_filters_to_allowed_services_only(self):
        """Test that only allowed services are returned (no peacock, hbo etc)"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        for opt in data["results"]:
            assert opt["service_id"] in ALLOWED_SERVICES, f"Service {opt['service_id']} should be filtered out"
    
    def test_service_display_mapping(self):
        """Test that services have proper display names (hbo -> Max, etc)"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        # Expected display names
        display_names = {
            "netflix": "Netflix",
            "prime": "Prime Video",
            "disney": "Disney+",
            "hulu": "Hulu",
            "apple": "Apple TV+",
            "hbo": "Max",
            "paramount": "Paramount+"
        }
        
        for opt in data["results"]:
            expected_name = display_names.get(opt["service_id"])
            if expected_name:
                assert opt["service_name"] == expected_name, f"Expected {expected_name}, got {opt['service_name']}"


class TestStreamingCountryCodes:
    """Tests for different country code handling"""
    
    def test_country_us(self):
        """Test US country code"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "us"
    
    def test_country_gb(self):
        """Test GB country code"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=gb")
        
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "gb"
        
        # Check if prices are in GBP
        rent_or_buy = [opt for opt in data["results"] if opt["type"] in ["rent", "buy"]]
        for opt in rent_or_buy:
            if "price_currency" in opt:
                assert opt["price_currency"] == "GBP"
    
    def test_country_ca(self):
        """Test CA (Canada) country code"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=ca")
        
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "ca"
    
    def test_country_code_normalized_lowercase(self):
        """Test that country codes are normalized to lowercase"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=US")
        
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "us"


class TestStreamingCache:
    """Tests for MongoDB caching functionality"""
    
    def test_cache_second_call(self):
        """Test that second call returns cached=true"""
        # First call (may or may not be cached)
        response1 = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        assert response1.status_code == 200
        
        # Second call should be cached
        response2 = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["cached"] == True, "Second call should return cached=true"
        print(f"Caching works: second call returned cached={data2['cached']}")
    
    def test_cache_returns_same_results(self):
        """Test that cached results are identical to fresh results"""
        response1 = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        response2 = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming?country=us")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Results should be identical
        assert data1["results"] == data2["results"], "Cached results should match original"
        assert data1["country"] == data2["country"]


class TestStreamingErrorHandling:
    """Tests for error handling and edge cases"""
    
    def test_invalid_movie_id_returns_empty(self):
        """Test that invalid movie ID returns empty results (not error)"""
        response = requests.get(f"{BASE_URL}/api/movies/{INVALID_MOVIE_ID}/streaming?country=us")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["results"] == []
        print(f"Invalid movie ID handled gracefully: returns empty results")
    
    def test_default_country_us(self):
        """Test that default country is 'us' when not specified"""
        # Note: The endpoint requires country param, but we can test with empty
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}/streaming")
        
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "us"  # Default should be 'us'


class TestMovieDetailIntegration:
    """Tests that movie detail endpoint still works correctly alongside streaming"""
    
    def test_movie_detail_has_required_fields(self):
        """Test movie detail endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields for movie detail
        assert "id" in data
        assert "title" in data
        assert "vote_average" in data
        assert "runtime" in data
        assert "genres" in data
        assert "overview" in data
        assert "cast" in data
        assert "similar" in data
        
        assert data["id"] == DARK_KNIGHT_ID
        assert data["title"] == "The Dark Knight"
        assert isinstance(data["genres"], list)
        assert isinstance(data["cast"], list)
        assert isinstance(data["similar"], list)
        
        print(f"Movie: {data['title']}, Rating: {data['vote_average']}, Runtime: {data['runtime']} min")
    
    def test_movie_detail_cast_structure(self):
        """Test cast array has proper structure"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cast"]) > 0
        
        for cast_member in data["cast"][:3]:
            assert "name" in cast_member
            assert "character" in cast_member
        
        print(f"Cast sample: {data['cast'][0]['name']} as {data['cast'][0]['character']}")
    
    def test_movie_detail_similar_structure(self):
        """Test similar movies array has proper structure"""
        response = requests.get(f"{BASE_URL}/api/movies/{DARK_KNIGHT_ID}")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["similar"]:
            for similar in data["similar"][:3]:
                assert "id" in similar
                assert "title" in similar
            
            print(f"Similar movies: {[s['title'] for s in data['similar'][:3]]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
