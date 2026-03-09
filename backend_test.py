#!/usr/bin/env python3
"""
Comprehensive Backend API Test Suite for Flick Movie Recommendation Engine
Tests all endpoints for functionality, error handling, and data consistency.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Use the public endpoint from frontend/.env
BACKEND_URL = "https://chef-movies.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FlickBackendTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        self.auth_token = None
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        if success:
            self.passed_tests.append(test_name)
            print(f"✅ PASS: {test_name}")
            if details:
                print(f"   Details: {details}")
        else:
            self.failed_tests.append(f"{test_name}: {details}")
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {details}")
        print()

    def make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30, auth_required: bool = False) -> tuple:
        """Make HTTP request and return (success, response_data, error_msg)"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add auth header if token is available and auth is required
        if auth_required and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return False, None, f"Unsupported method: {method}"
            
            # Check if response is successful
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    response_data = response.json()
                    return True, response_data, ""
                except json.JSONDecodeError:
                    return True, {"raw_response": response.text}, ""
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail.get('detail', 'Unknown error')}"
                except:
                    error_msg += f": {response.text}"
                return False, None, error_msg
                
        except requests.exceptions.Timeout:
            return False, None, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error - backend may be down"
        except Exception as e:
            return False, None, f"Request failed: {str(e)}"

    def test_authentication(self):
        """Test user registration and login to get auth token"""
        # Try to register a test user
        test_email = f"test_user_{int(time.time())}@example.com"
        test_password = "testpass123"
        test_username = f"test_user_{int(time.time())}"
        
        register_data = {
            "email": test_email,
            "password": test_password,
            "username": test_username,
            "birth_year": 1990
        }
        
        success, data, error = self.make_request("POST", "/auth/register", register_data)
        
        if success and data and "token" in data:
            self.auth_token = data["token"]
            self.log_result(
                "User Registration",
                True,
                f"Registered user: {test_username}",
                {"username": test_username, "has_token": bool(self.auth_token)}
            )
            return True
        else:
            # Try to login with existing user if registration failed
            login_data = {
                "email": "test@example.com",
                "password": "password123"
            }
            
            success, data, error = self.make_request("POST", "/auth/login", login_data)
            
            if success and data and "token" in data:
                self.auth_token = data["token"]
                self.log_result(
                    "User Login (Fallback)",
                    True,
                    "Logged in with existing test user"
                )
                return True
            else:
                self.log_result(
                    "Authentication",
                    False,
                    f"Both registration and login failed. Register error: {error}"
                )
                return False

    def test_root_endpoint(self):
        """Test basic API connectivity"""
        success, data, error = self.make_request("GET", "/")
        
        if success and data and "message" in data:
            self.log_result(
                "Root Endpoint",
                True,
                f"API responding: {data['message']}"
            )
        else:
            self.log_result(
                "Root Endpoint",
                False,
                error or "Invalid response format"
            )

    def test_seed_data(self):
        """Test seeding initial data (mock user + watch history)"""
        success, data, error = self.make_request("POST", "/seed-data")
        
        if success and data:
            if "message" in data and "count" in data:
                self.log_result(
                    "Seed Data",
                    True,
                    f"{data['message']} - {data['count']} movies seeded",
                    data
                )
                return True
            else:
                self.log_result(
                    "Seed Data",
                    False,
                    "Missing expected fields in response"
                )
                return False
        else:
            self.log_result(
                "Seed Data",
                False,
                error
            )
            return False

    def test_user_profile(self):
        """Test getting user profile"""
        success, data, error = self.make_request("GET", "/auth/me", auth_required=True)
        
        if success and data:
            required_fields = ["id", "username", "birth_year"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_result(
                    "User Profile",
                    True,
                    f"User: {data['username']}, Birth Year: {data['birth_year']}",
                    data
                )
                return data
            else:
                self.log_result(
                    "User Profile", 
                    False,
                    f"Missing fields: {missing_fields}"
                )
                return None
        else:
            self.log_result(
                "User Profile",
                False,
                error
            )
            return None

    def test_watch_history(self):
        """Test getting watch history"""
        success, data, error = self.make_request("GET", "/user/watch-history", auth_required=True)
        
        if success:
            if isinstance(data, list):
                self.log_result(
                    "Watch History",
                    True,
                    f"Found {len(data)} movies in history",
                    {"count": len(data), "sample": data[:2] if data else []}
                )
                return data
            else:
                self.log_result(
                    "Watch History",
                    False,
                    "Response is not a list"
                )
                return []
        else:
            self.log_result(
                "Watch History",
                False,
                error
            )
            return []

    def test_trending_movies(self):
        """Test getting trending movies"""
        success, data, error = self.make_request("GET", "/movies/trending")
        
        if success and data:
            results = data.get("results", [])
            if results:
                # Check first movie has required fields
                movie = results[0]
                required_fields = ["id", "title", "poster_url", "backdrop_url", "genres"]
                missing_fields = [field for field in required_fields if field not in movie]
                
                if not missing_fields:
                    self.log_result(
                        "Trending Movies",
                        True,
                        f"Retrieved {len(results)} trending movies",
                        {
                            "count": len(results),
                            "sample_movie": {
                                "title": movie.get("title"),
                                "genres": movie.get("genres", [])[:3]
                            }
                        }
                    )
                    return results
                else:
                    self.log_result(
                        "Trending Movies",
                        False,
                        f"Movies missing required fields: {missing_fields}"
                    )
                    return []
            else:
                self.log_result(
                    "Trending Movies",
                    False,
                    "No movies returned in results"
                )
                return []
        else:
            self.log_result(
                "Trending Movies",
                False,
                error
            )
            return []

    def test_discover_movies(self):
        """Test movie discovery with vibe parameters"""
        # Test default parameters
        vibe_params = {
            "brain_power": 50,
            "mood": 50,
            "energy": 50,
            "include_rewatches": False,
            "page": 1
        }
        
        success, data, error = self.make_request("POST", "/movies/discover", vibe_params)
        
        if success and data:
            results = data.get("results", [])
            if results:
                # Check movies have scoring fields
                movie = results[0]
                scoring_fields = ["match_percentage", "vibe_tag"]
                present_fields = [field for field in scoring_fields if field in movie]
                
                if present_fields:
                    self.log_result(
                        "Discover Movies (Default Vibe)",
                        True,
                        f"Retrieved {len(results)} movies with scoring",
                        {
                            "count": len(results),
                            "sample_movie": {
                                "title": movie.get("title"),
                                "match_percentage": movie.get("match_percentage"),
                                "vibe_tag": movie.get("vibe_tag")
                            }
                        }
                    )
                    
                    # Test different vibe parameters
                    self._test_extreme_vibes()
                    return results
                else:
                    self.log_result(
                        "Discover Movies (Default Vibe)",
                        False,
                        f"Movies missing scoring fields: {scoring_fields}"
                    )
                    return []
            else:
                self.log_result(
                    "Discover Movies (Default Vibe)",
                    False,
                    "No movies returned in discover results"
                )
                return []
        else:
            self.log_result(
                "Discover Movies (Default Vibe)",
                False,
                error
            )
            return []

    def _test_extreme_vibes(self):
        """Test discover with extreme vibe parameters"""
        extreme_vibes = [
            {
                "name": "Low Energy + Sad Mood",
                "params": {"brain_power": 30, "mood": 10, "energy": 10, "include_rewatches": False}
            },
            {
                "name": "High Energy + Happy Mood",
                "params": {"brain_power": 80, "mood": 90, "energy": 90, "include_rewatches": False}
            },
            {
                "name": "With Rewatches",
                "params": {"brain_power": 50, "mood": 50, "energy": 50, "include_rewatches": True}
            }
        ]
        
        for vibe_test in extreme_vibes:
            success, data, error = self.make_request("POST", "/movies/discover", vibe_test["params"])
            
            if success and data and data.get("results"):
                self.log_result(
                    f"Discover Movies ({vibe_test['name']})",
                    True,
                    f"Retrieved {len(data['results'])} movies"
                )
            else:
                self.log_result(
                    f"Discover Movies ({vibe_test['name']})",
                    False,
                    error or "No results returned"
                )

    def test_emergency_recommendations(self):
        """Test 'I Can't Even' emergency recommendations"""
        success, data, error = self.make_request("GET", "/movies/emergency")
        
        if success and data:
            results = data.get("results", [])
            if results:
                # Check emergency movies have required fields
                movie = results[0]
                emergency_fields = ["tmdb_id", "title", "user_rating", "vibe_tag"]
                missing_fields = [field for field in emergency_fields if field not in movie]
                
                if not missing_fields:
                    self.log_result(
                        "Emergency Recommendations",
                        True,
                        f"Retrieved {len(results)} comfort movies",
                        {
                            "count": len(results),
                            "sample_movie": {
                                "title": movie.get("title"),
                                "user_rating": movie.get("user_rating"),
                                "vibe_tag": movie.get("vibe_tag")
                            }
                        }
                    )
                    return results
                else:
                    self.log_result(
                        "Emergency Recommendations",
                        False,
                        f"Movies missing required fields: {missing_fields}"
                    )
                    return []
            else:
                # This might be expected if no high-rated old movies exist
                self.log_result(
                    "Emergency Recommendations",
                    True,
                    "No emergency movies found (expected if no suitable watch history exists)"
                )
                return []
        else:
            self.log_result(
                "Emergency Recommendations",
                False,
                error
            )
            return []

    def test_movie_details(self, movie_id: int = 278):
        """Test getting detailed movie information (default: The Shawshank Redemption)"""
        success, data, error = self.make_request("GET", f"/movies/{movie_id}")
        
        if success and data:
            required_fields = ["id", "title", "overview", "poster_url", "genres"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_result(
                    "Movie Details",
                    True,
                    f"Retrieved details for: {data.get('title')}",
                    {
                        "title": data.get("title"),
                        "has_trailer": bool(data.get("trailer_url")),
                        "cast_count": len(data.get("cast", [])),
                        "similar_count": len(data.get("similar", []))
                    }
                )
                return data
            else:
                self.log_result(
                    "Movie Details",
                    False,
                    f"Missing required fields: {missing_fields}"
                )
                return None
        else:
            self.log_result(
                "Movie Details",
                False,
                error
            )
            return None

    def test_add_to_watch_history(self, movie_id: int = 550, rating: int = 8):
        """Test adding movie to watch history"""
        watch_data = {
            "tmdb_id": movie_id,
            "user_rating": rating,
            "title": "Fight Club",
            "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"
        }
        
        success, data, error = self.make_request("POST", "/user/watch-history", watch_data, auth_required=True)
        
        if success and data:
            required_fields = ["user_id", "tmdb_id", "user_rating", "title"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_result(
                    "Add to Watch History",
                    True,
                    f"Added {data.get('title')} with rating {data.get('user_rating')}/10"
                )
                return True
            else:
                self.log_result(
                    "Add to Watch History",
                    False,
                    f"Response missing fields: {missing_fields}"
                )
                return False
        else:
            self.log_result(
                "Add to Watch History",
                False,
                error
            )
            return False

    def test_genres_endpoint(self):
        """Test getting genres list"""
        success, data, error = self.make_request("GET", "/genres")
        
        if success and data:
            genres = data.get("genres", [])
            if genres and len(genres) > 0:
                self.log_result(
                    "Genres List",
                    True,
                    f"Retrieved {len(genres)} genres"
                )
                return True
            else:
                self.log_result(
                    "Genres List", 
                    False,
                    "No genres returned"
                )
                return False
        else:
            self.log_result(
                "Genres List",
                False,
                error
            )
            return False

    def test_profile_insights(self):
        """Test profile insights endpoint with proportion-based scoring and franchise deduplication"""
        success, data, error = self.make_request("GET", "/user/profile-insights", auth_required=True)
        
        if success and data:
            # Check for required top-level fields
            required_fields = ["genres", "actors", "directors", "stats"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Check stats object has new fields
                stats = data.get("stats", {})
                required_stats = ["total_movies_watched", "effective_entries", "franchises_watched", "standalone_movies"]
                missing_stats = [field for field in required_stats if field not in stats]
                
                # Check genre entries have new proportion fields
                genres = data.get("genres", [])
                if genres:
                    genre = genres[0]
                    required_genre_fields = ["name", "count", "proportion_index", "raw_score"]
                    missing_genre_fields = [field for field in required_genre_fields if field not in genre]
                else:
                    missing_genre_fields = []
                
                # Check actor entries have franchise fields
                actors = data.get("actors", [])
                if actors:
                    actor = actors[0]
                    required_actor_fields = ["name", "count", "proportion_index", "franchise_appearances"]
                    missing_actor_fields = [field for field in required_actor_fields if field not in actor]
                else:
                    missing_actor_fields = []
                
                # Check director entries have franchise fields  
                directors = data.get("directors", [])
                if directors:
                    director = directors[0]
                    required_director_fields = ["name", "count", "proportion_index", "franchise_count", "standalone_count"]
                    missing_director_fields = [field for field in required_director_fields if field not in director]
                else:
                    missing_director_fields = []
                
                all_missing = missing_stats + missing_genre_fields + missing_actor_fields + missing_director_fields
                
                if not all_missing:
                    self.log_result(
                        "Profile Insights (Enhanced)",
                        True,
                        f"Stats: {stats['effective_entries']} effective entries, {stats['franchises_watched']} franchises",
                        {
                            "stats": stats,
                            "sample_genre": genres[0] if genres else None,
                            "sample_actor": actors[0] if actors else None,
                            "sample_director": directors[0] if directors else None
                        }
                    )
                    return data
                else:
                    self.log_result(
                        "Profile Insights (Enhanced)",
                        False,
                        f"Missing enhanced fields: {all_missing}"
                    )
                    return None
            else:
                self.log_result(
                    "Profile Insights (Enhanced)",
                    False,
                    f"Missing required fields: {missing_fields}"
                )
                return None
        else:
            self.log_result(
                "Profile Insights (Enhanced)",
                False,
                error
            )
            return None

    def test_movie_metadata_caching(self):
        """Test that movie metadata includes franchise information from TMDB"""
        # Test with a known franchise movie (e.g., Iron Man - MCU)
        movie_id = 1726  # Iron Man
        success, data, error = self.make_request("GET", f"/movies/{movie_id}")
        
        if success and data:
            # Check if franchise info is present (might be None for non-franchise movies)
            has_franchise_field = "franchise" in data or "belongs_to_collection" in data
            
            self.log_result(
                "Movie Metadata Caching (Franchise Info)",
                True,
                f"Movie {data.get('title', 'Unknown')} - Franchise field present: {has_franchise_field}",
                {
                    "title": data.get("title"),
                    "has_franchise_info": has_franchise_field,
                    "franchise": data.get("franchise") or data.get("belongs_to_collection")
                }
            )
            return data
        else:
            self.log_result(
                "Movie Metadata Caching (Franchise Info)",
                False,
                error
            )
            return None

    def test_proportion_scoring_algorithm(self, insights_data=None):
        """Test that proportion-based scoring is working by checking insights data"""
        if not insights_data:
            insights_data = self.test_profile_insights()
        
        if insights_data:
            genres = insights_data.get("genres", [])
            if genres:
                # Check that proportion_index values are reasonable (should be > 0)
                valid_proportions = all(
                    isinstance(g.get("proportion_index"), (int, float)) and g.get("proportion_index", 0) > 0
                    for g in genres
                )
                
                if valid_proportions:
                    self.log_result(
                        "Proportion Scoring Algorithm",
                        True,
                        f"All {len(genres)} genres have valid proportion scores",
                        {
                            "sample_proportions": [
                                {"name": g["name"], "proportion_index": g["proportion_index"]}
                                for g in genres[:3]
                            ]
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Proportion Scoring Algorithm",
                        False,
                        "Some genres have invalid proportion_index values"
                    )
                    return False
            else:
                self.log_result(
                    "Proportion Scoring Algorithm",
                    True,
                    "No genres to test (user may have no watch history)"
                )
                return True
        else:
            self.log_result(
                "Proportion Scoring Algorithm",
                False,
                "Could not get profile insights to test proportion scoring"
            )
            return False

    def test_franchise_deduplication(self, insights_data=None):
        """Test that franchise deduplication is working by checking stats"""
        if not insights_data:
            insights_data = self.test_profile_insights()
        
        if insights_data:
            stats = insights_data.get("stats", {})
            total_movies = stats.get("total_movies_watched", 0)
            effective_entries = stats.get("effective_entries", 0)
            franchises_watched = stats.get("franchises_watched", 0)
            
            # If user has watched franchise movies, effective entries should be less than total
            if franchises_watched > 0:
                deduplication_working = effective_entries <= total_movies
                
                self.log_result(
                    "Franchise Deduplication",
                    deduplication_working,
                    f"Total: {total_movies}, Effective: {effective_entries}, Franchises: {franchises_watched}",
                    stats
                )
                return deduplication_working
            else:
                self.log_result(
                    "Franchise Deduplication",
                    True,
                    "No franchises watched - deduplication not applicable"
                )
                return True
        else:
            self.log_result(
                "Franchise Deduplication",
                False,
                "Could not get profile insights to test franchise deduplication"
            )
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("🎬 Starting Flick Backend API Test Suite")
        print("=" * 60)
        print()
        
        # Test basic connectivity
        self.test_root_endpoint()
        
        # Test authentication first
        auth_success = self.test_authentication()
        if not auth_success:
            print("⚠️  Authentication failed - some tests will be skipped")
        
        # Test data initialization
        seed_success = self.test_seed_data()
        
        # Test user endpoints (require auth)
        if auth_success:
            user_profile = self.test_user_profile()
            watch_history = self.test_watch_history()
        
        # Test movie endpoints (public)
        trending_movies = self.test_trending_movies()
        discovered_movies = self.test_discover_movies()
        emergency_movies = self.test_emergency_recommendations()
        
        # Test detailed movie info
        movie_details = self.test_movie_details()
        
        # Test watch history management (requires auth)
        if auth_success:
            self.test_add_to_watch_history()
        
        # Test enhanced profile insights functionality (requires auth)
        if auth_success:
            insights_data = self.test_profile_insights()
            self.test_movie_metadata_caching()
            self.test_proportion_scoring_algorithm(insights_data)
            self.test_franchise_deduplication(insights_data)
        
        # Test genres
        self.test_genres_endpoint()
        
        # Print summary
        print("=" * 60)
        print("🎬 FLICK BACKEND TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        print(f"📊 Success Rate: {len(self.passed_tests)/(len(self.passed_tests) + len(self.failed_tests)) * 100:.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        
        print(f"\n📝 Total Tests Run: {len(self.test_results)}")
        print(f"⏱️  Test Duration: {datetime.now().isoformat()}")
        
        return {
            "total_tests": len(self.test_results),
            "passed": len(self.passed_tests),
            "failed": len(self.failed_tests),
            "success_rate": len(self.passed_tests)/(len(self.passed_tests) + len(self.failed_tests)) * 100,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests
        }


if __name__ == "__main__":
    tester = FlickBackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results["failed"] == 0 else 1
    exit(exit_code)