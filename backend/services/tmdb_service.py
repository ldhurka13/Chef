"""
TMDB API service - requests, caching, image URLs, genre mapping.
"""
import time
import json
import logging
import requests
from typing import Optional, Dict
from config import TMDB_API_KEY, TMDB_BASE_URL, IMAGE_BASE_URL, CACHE_TTL

# Cache for TMDB requests
tmdb_cache = {}

# Genre mapping (loaded at startup)
GENRE_MAP = {}

# Genre categorization for complexity/mood
LOW_ENERGY_GENRES = {"Documentary", "History", "War", "Drama"}
HIGH_ENERGY_GENRES = {"Animation", "Comedy", "Adventure", "Action"}
FEEL_GOOD_GENRES = {"Comedy", "Animation", "Family", "Romance", "Musical"}
INTENSE_GENRES = {"Thriller", "Horror", "Crime", "Drama", "War"}

# Complexity scores by genre
GENRE_COMPLEXITY = {
    "Documentary": 8, "History": 7, "War": 6, "Drama": 5,
    "Science Fiction": 6, "Mystery": 6, "Thriller": 5,
    "Comedy": 3, "Animation": 3, "Adventure": 4, "Action": 3,
    "Romance": 4, "Family": 2, "Fantasy": 4, "Horror": 4,
    "Crime": 5, "Music": 3, "Musical": 3, "Western": 4
}


def tmdb_request(endpoint: str, params: dict = None, ttl: int = CACHE_TTL) -> Optional[dict]:
    """Make a cached request to TMDB API"""
    params = params or {}
    cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
    
    # Check cache
    cached = tmdb_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < ttl:
        return cached["data"]
    
    url = f"{TMDB_BASE_URL}{endpoint}"
    params = {"api_key": TMDB_API_KEY, **params}
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 429:
            time.sleep(int(res.headers.get("Retry-After", 2)))
            res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
    except Exception as e:
        logging.error(f"TMDB request failed: {e}")
        return None
    
    data = res.json()
    tmdb_cache[cache_key] = {"data": data, "ts": time.time()}
    return data


def get_image_url(path: str, size: str = "w500") -> Optional[str]:
    """Get full image URL from TMDB path"""
    return f"{IMAGE_BASE_URL}{size}{path}" if path else None


def get_genres() -> Dict[int, str]:
    """Get genre mapping from TMDB"""
    data = tmdb_request("/genre/movie/list", ttl=86400)
    if data:
        return {g["id"]: g["name"] for g in data.get("genres", [])}
    return {}


def load_genre_map():
    """Load genre map at startup"""
    global GENRE_MAP
    GENRE_MAP = get_genres()
    return GENRE_MAP


def get_genre_map() -> Dict[int, str]:
    """Get current genre map"""
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    return GENRE_MAP
