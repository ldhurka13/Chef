#!/usr/bin/env python3
import requests
import json

BACKEND_URL = "https://chef-movies.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Register a test user
test_email = f"rewatch_test@example.com"
test_password = "testpass123"
test_username = f"rewatch_test"

register_data = {
    "email": test_email,
    "password": test_password,
    "username": test_username,
    "birth_year": 1990
}

print("Registering user...")
response = requests.post(f"{API_BASE}/auth/register", json=register_data)
print(f"Register response: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    token = data.get("token")
    print(f"Got token: {token[:20]}...")
    
    # Add a movie to watch history
    watch_data = {
        "tmdb_id": 550,
        "user_rating": 8.5,
        "title": "Fight Club",
        "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg"
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\nAdding movie to watch history...")
    response = requests.post(f"{API_BASE}/user/watch-history", json=watch_data, headers=headers)
    print(f"Add movie response: {response.status_code}")
    
    # Test discover with rewatches
    vibe_params = {
        "brain_power": 50,
        "mood": 50,
        "energy": 50,
        "include_rewatches": True,
        "page": 1
    }
    
    print("\nTesting discover with rewatches...")
    response = requests.post(f"{API_BASE}/movies/discover", json=vibe_params, headers=headers)
    print(f"Discover with rewatches response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Got {len(data.get('results', []))} movies")
    else:
        print(f"Error: {response.text}")
        
else:
    print(f"Registration failed: {response.text}")