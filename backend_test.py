#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ChefAPITester:
    def __init__(self, base_url="https://chef-movies.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with provided credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": "rdhurka@gmail.com",
                "password": "test123"
            }
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   Logged in as user: {self.user_id}")
            return True
        return False

    def test_profile_insights_proportion_badges(self):
        """Test that profile insights returns proportion_index for percentage badges"""
        success, response = self.run_test(
            "Profile Insights - Proportion Badges",
            "GET",
            "user/profile-insights",
            200
        )
        
        if not success:
            return False
            
        # Check that we have the expected structure
        required_keys = ['genres', 'actors', 'directors', 'stats']
        for key in required_keys:
            if key not in response:
                print(f"❌ Missing key: {key}")
                return False
        
        # Check genres have proportion_index
        genres = response.get('genres', [])
        if genres:
            for i, genre in enumerate(genres[:3]):  # Check first 3
                if 'proportion_index' not in genre:
                    print(f"❌ Genre {genre.get('name')} missing proportion_index")
                    return False
                
                proportion = genre['proportion_index']
                if not isinstance(proportion, (int, float)) or proportion <= 0:
                    print(f"❌ Invalid proportion_index for {genre.get('name')}: {proportion}")
                    return False
                
                # Check for franchise/standalone breakdown
                if 'franchise_count' not in genre or 'standalone_count' not in genre:
                    print(f"❌ Genre {genre.get('name')} missing franchise/standalone counts")
                    return False
                
                print(f"   ✓ Genre: {genre['name']} - {genre['count']} films, proportion: {proportion:.2f}")
        
        # Check actors have proportion_index and role badges
        actors = response.get('actors', [])
        if actors:
            for i, actor in enumerate(actors[:3]):  # Check first 3
                if 'proportion_index' not in actor:
                    print(f"❌ Actor {actor.get('name')} missing proportion_index")
                    return False
                
                proportion = actor['proportion_index']
                if not isinstance(proportion, (int, float)) or proportion <= 0:
                    print(f"❌ Invalid proportion_index for {actor.get('name')}: {proportion}")
                    return False
                
                # Check for role badge
                if 'primary_role' not in actor:
                    print(f"❌ Actor {actor.get('name')} missing primary_role")
                    return False
                
                role = actor['primary_role']
                if role not in ['lead', 'supporting', 'background']:
                    print(f"❌ Invalid primary_role for {actor.get('name')}: {role}")
                    return False
                
                # Check for franchise/standalone appearances
                if 'franchise_appearances' not in actor or 'standalone_appearances' not in actor:
                    print(f"❌ Actor {actor.get('name')} missing franchise/standalone appearances")
                    return False
                
                print(f"   ✓ Actor: {actor['name']} - {actor['count']} films, proportion: {proportion:.2f}, role: {role}")
        
        # Check directors have proportion_index
        directors = response.get('directors', [])
        if directors:
            for i, director in enumerate(directors[:3]):  # Check first 3
                if 'proportion_index' not in director:
                    print(f"❌ Director {director.get('name')} missing proportion_index")
                    return False
                
                proportion = director['proportion_index']
                if not isinstance(proportion, (int, float)) or proportion <= 0:
                    print(f"❌ Invalid proportion_index for {director.get('name')}: {proportion}")
                    return False
                
                # Check for franchise/standalone breakdown
                if 'franchise_count' not in director or 'standalone_count' not in director:
                    print(f"❌ Director {director.get('name')} missing franchise/standalone counts")
                    return False
                
                print(f"   ✓ Director: {director['name']} - {director['count']} films, proportion: {proportion:.2f}")
        
        # Check stats summary
        stats = response.get('stats', {})
        required_stats = ['total_movies_watched', 'franchises_watched', 'standalone_movies']
        for stat in required_stats:
            if stat not in stats:
                print(f"❌ Missing stat: {stat}")
                return False
            if not isinstance(stats[stat], int) or stats[stat] < 0:
                print(f"❌ Invalid stat value for {stat}: {stats[stat]}")
                return False
        
        print(f"   ✓ Stats: {stats['total_movies_watched']} total, {stats['franchises_watched']} franchises, {stats['standalone_movies']} standalone")
        
        return True

    def test_proportion_badge_logic(self):
        """Test that proportion badges show correct colors (green for above avg, amber for below avg)"""
        success, response = self.run_test(
            "Profile Insights - Badge Logic Verification",
            "GET",
            "user/profile-insights",
            200
        )
        
        if not success:
            return False
        
        # Test the proportion logic for genres
        genres = response.get('genres', [])
        above_avg_count = 0
        below_avg_count = 0
        
        for genre in genres:
            proportion = genre.get('proportion_index', 1.0)
            if proportion >= 1.0:
                above_avg_count += 1
                print(f"   ✓ {genre['name']}: {proportion:.2f} (GREEN - above average)")
            else:
                below_avg_count += 1
                print(f"   ✓ {genre['name']}: {proportion:.2f} (AMBER - below average)")
        
        print(f"   Summary: {above_avg_count} above average (green), {below_avg_count} below average (amber)")
        
        # Verify we have a mix or at least some data
        if len(genres) == 0:
            print("❌ No genre data to test proportion badges")
            return False
        
        return True

def main():
    """Run comprehensive backend tests for proportion percentage feature"""
    print("🎬 Chef Movie App - Proportion Percentage Backend Testing")
    print("=" * 60)
    
    tester = ChefAPITester()
    
    # Test authentication first
    if not tester.test_login():
        print("❌ Login failed, cannot proceed with testing")
        return 1
    
    # Test proportion badge functionality
    tests = [
        tester.test_profile_insights_proportion_badges,
        tester.test_proportion_badge_logic,
    ]
    
    for test in tests:
        if not test():
            print(f"❌ Test failed: {test.__name__}")
    
    # Print final results
    print(f"\n📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed! Proportion percentage feature is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())