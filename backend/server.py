from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Header, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import math
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import requests
import httpx
import time
import json
import hashlib
import secrets
import asyncio
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# TMDB Configuration
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"

# Streaming Availability API (Movies of the Night)
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY')
STREAMING_API_BASE = "https://streaming-availability.p.rapidapi.com"
ALLOWED_SERVICES = {"netflix", "prime", "disney", "hulu", "apple", "hbo", "paramount"}

# Resend email config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Cache for TMDB requests
tmdb_cache = {}
CACHE_TTL = 3600  # 1 hour

# JWT Secret (simple implementation)
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))

# Create the main app
app = FastAPI(title="Chef - Movie Recommendation Engine")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    birth_year: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WatchHistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tmdb_id: int
    user_rating: float = Field(ge=0, le=10)
    watch_dates: List[str] = []
    last_watched_date: str = ""
    watch_count: int = 1
    title: str = ""
    poster_path: Optional[str] = None

class WatchHistoryCreate(BaseModel):
    tmdb_id: int
    user_rating: float = Field(ge=0, le=10)
    watched_date: Optional[str] = None
    title: str = ""
    poster_path: Optional[str] = None

class WatchHistoryUpdate(BaseModel):
    user_rating: Optional[float] = Field(default=None, ge=0, le=10)
    watched_date: Optional[str] = None

class WatchEntryCreate(BaseModel):
    rating: float = Field(ge=0, le=10, default=7.0)
    date: Optional[str] = None
    comment: Optional[str] = None

class WatchEntryUpdate(BaseModel):
    rating: Optional[float] = Field(default=None, ge=0, le=10)
    date: Optional[str] = None
    comment: Optional[str] = None

class MovieMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tmdb_id: int
    title: str
    complexity_score: int = Field(ge=1, le=10, default=5)
    release_year: Optional[int] = None
    genres: List[str] = []

class VibeParams(BaseModel):
    brain_power: int = Field(ge=0, le=100, default=50)  # Complexity
    mood: int = Field(ge=0, le=100, default=50)  # Drama/Thriller vs Comedy
    energy: int = Field(ge=0, le=100, default=50)  # Pacing/Action
    include_rewatches: bool = False
    page: int = 1

# ============ AUTH MODELS ============

class UserRegister(BaseModel):
    email: str
    password: str
    username: str
    birth_year: int = 1995
    birth_date: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    birth_year: int = 1995
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    favorite_genres: List[str] = []

class UserUpdate(BaseModel):
    username: Optional[str] = None
    birth_year: Optional[int] = None
    birth_date: Optional[str] = None
    avatar_url: Optional[str] = None
    favorite_genres: Optional[List[str]] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    favorite_actors: Optional[List[str]] = None
    favorite_movies: Optional[List[Dict[str, Any]]] = None
    streaming_services: Optional[List[str]] = None
    favorite_directors: Optional[List[str]] = None

class WatchlistAdd(BaseModel):
    tmdb_id: int
    title: str = ""
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    genres: Optional[List[str]] = None

class LocationPermissionUpdate(BaseModel):
    location_permission: str  # "always", "ask", "never"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = JWT_SECRET[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_token(user_id: str) -> str:
    """Create a simple token (user_id:timestamp:signature)"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}"
    signature = hashlib.sha256(f"{data}:{JWT_SECRET}".encode()).hexdigest()[:16]
    return f"{data}:{signature}"

def verify_token(token: str) -> Optional[str]:
    """Verify token and return user_id if valid"""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        user_id, timestamp, signature = parts
        # Check signature
        data = f"{user_id}:{timestamp}"
        expected_sig = hashlib.sha256(f"{data}:{JWT_SECRET}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return None
        # Check expiration (7 days)
        if int(time.time()) - int(timestamp) > 7 * 24 * 3600:
            return None
        return user_id
    except:
        return None

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get current user from token"""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    if not user_id:
        return None
    
    user = await db.auth_users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return user

# ============ TMDB SERVICE ============

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

GENRE_MAP = {}

# ============ ACTOR IMPACT ALGORITHM ============
# Role classification thresholds based on cast order
LEAD_ACTOR_THRESHOLD = 3      # Order 0-2 are leads (top 3 billed)
SUPPORTING_ACTOR_THRESHOLD = 10  # Order 3-9 are supporting

def classify_actor_role(order: int, total_cast: int) -> str:
    """
    Classify actor role based on billing order.
    Returns: 'lead', 'supporting', or 'background'
    """
    if order < LEAD_ACTOR_THRESHOLD:
        return 'lead'
    elif order < SUPPORTING_ACTOR_THRESHOLD:
        return 'supporting'
    return 'background'

def calculate_actor_impact(
    actor_order: int,
    total_cast: int,
    num_leads: int = 3,
    num_supporting: int = 7,
    actor_filmography_count: int = 1,
    actor_popularity: float = 0.0
) -> dict:
    """
    Calculate an actor's impact on a movie based on:
    - Role (lead/supporting/background)
    - Number of actors in each role category
    - Actor's experience (filmography count)
    - Actor's popularity
    
    Returns dict with role, base_impact, adjusted_impact, and final_impact
    """
    # Base impact weights
    BASE_LEAD_IMPACT = 1.0
    BASE_SUPPORTING_IMPACT = 0.5
    BASE_BACKGROUND_IMPACT = 0.15
    
    # Classify role
    role = classify_actor_role(actor_order, total_cast)
    
    # Calculate divisor based on role
    num_background = max(total_cast - num_leads - num_supporting, 1)
    
    if role == 'lead':
        base_impact = BASE_LEAD_IMPACT
        divisor = max(num_leads, 1)
    elif role == 'supporting':
        base_impact = BASE_SUPPORTING_IMPACT
        divisor = max(num_leads + num_supporting, 1)
    else:  # background
        base_impact = BASE_BACKGROUND_IMPACT
        divisor = max(num_leads + num_supporting + num_background, 1)
    
    # Adjusted impact by role count
    adjusted_impact = base_impact / divisor
    
    # Experience multiplier (logarithmic scale to prevent extreme values)
    # An actor with 50+ films gets ~2x boost, 10 films ~1.5x
    experience_multiplier = 1.0 + (math.log10(max(actor_filmography_count, 1) + 1) * 0.5)
    
    # Popularity multiplier (normalized 0-1 scale, TMDB popularity is usually 0-100+)
    # Cap at 2x for extremely popular actors
    popularity_multiplier = 1.0 + min(actor_popularity / 100.0, 1.0)
    
    # Final impact combines all factors
    final_impact = adjusted_impact * experience_multiplier * popularity_multiplier
    
    return {
        "role": role,
        "order": actor_order,
        "base_impact": round(base_impact, 3),
        "divisor": divisor,
        "adjusted_impact": round(adjusted_impact, 3),
        "experience_multiplier": round(experience_multiplier, 3),
        "popularity_multiplier": round(popularity_multiplier, 3),
        "final_impact": round(final_impact, 4)
    }

def count_cast_by_role(cast_list: list) -> dict:
    """
    Count actors in each role category from a cast list.
    Cast list should have 'order' field from TMDB.
    """
    num_leads = sum(1 for c in cast_list if c.get("order", 999) < LEAD_ACTOR_THRESHOLD)
    num_supporting = sum(1 for c in cast_list if LEAD_ACTOR_THRESHOLD <= c.get("order", 999) < SUPPORTING_ACTOR_THRESHOLD)
    num_background = sum(1 for c in cast_list if c.get("order", 999) >= SUPPORTING_ACTOR_THRESHOLD)
    
    return {
        "num_leads": max(num_leads, 1),  # At least 1 to avoid division by zero
        "num_supporting": max(num_supporting, 0),
        "num_background": max(num_background, 0),
        "total": len(cast_list)
    }

async def get_actor_stats(actor_name: str) -> dict:
    """
    Get actor's filmography count and popularity from local DB or TMDB.
    Returns dict with filmography_count and popularity.
    """
    # First check local movies DB for filmography count
    filmography_count = await db.movies.count_documents({
        "stars": {"$regex": f"^{actor_name}$", "$options": "i"}
    })
    
    # Try TMDB search for popularity if we have API key
    popularity = 0.0
    tmdb_api_key = os.environ.get("TMDB_API_KEY")
    if tmdb_api_key and filmography_count < 5:
        # Only hit TMDB if local data is sparse
        try:
            res = requests.get(
                f"{TMDB_BASE_URL}/search/person",
                params={"api_key": tmdb_api_key, "query": actor_name},
                timeout=5
            )
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    popularity = results[0].get("popularity", 0.0)
                    # Also update filmography count from TMDB
                    known_for = results[0].get("known_for", [])
                    filmography_count = max(filmography_count, len(known_for))
        except:
            pass
    
    return {
        "filmography_count": filmography_count,
        "popularity": popularity
    }

# Actor stats cache to avoid repeated lookups
_actor_stats_cache = {}

async def get_cached_actor_stats(actor_name: str) -> dict:
    """Cached version of get_actor_stats."""
    if actor_name not in _actor_stats_cache:
        _actor_stats_cache[actor_name] = await get_actor_stats(actor_name)
    return _actor_stats_cache[actor_name]

# ============ PROPORTION-BASED SCORING ============
# Cache for total counts in database (refreshed periodically)
_total_counts_cache = {
    "genres": {},
    "actors": {},
    "directors": {},
    "last_updated": None
}

async def get_total_counts():
    """
    Get total count of movies for each genre, actor, and director in the database.
    Used to calculate proportions for fair comparisons.
    Cached for 1 hour to avoid repeated DB queries.
    """
    from datetime import datetime, timedelta
    
    # Check if cache is fresh (less than 1 hour old)
    if _total_counts_cache["last_updated"]:
        age = datetime.now(timezone.utc) - _total_counts_cache["last_updated"]
        if age < timedelta(hours=1):
            return _total_counts_cache
    
    # Count movies per genre
    genre_pipeline = [
        {"$unwind": "$genres"},
        {"$group": {"_id": "$genres", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    genre_counts = {}
    async for doc in db.movies.aggregate(genre_pipeline):
        genre_counts[doc["_id"]] = doc["count"]
    
    # Count movies per actor (from stars field)
    actor_pipeline = [
        {"$unwind": "$stars"},
        {"$group": {"_id": "$stars", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 3}}},  # Only actors with 3+ movies
        {"$sort": {"count": -1}},
        {"$limit": 10000}  # Limit to top 10k actors
    ]
    actor_counts = {}
    async for doc in db.movies.aggregate(actor_pipeline):
        actor_counts[doc["_id"]] = doc["count"]
    
    # Count movies per director
    director_pipeline = [
        {"$unwind": "$directors"},
        {"$group": {"_id": "$directors", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 2}}},  # Only directors with 2+ movies
        {"$sort": {"count": -1}},
        {"$limit": 5000}
    ]
    director_counts = {}
    async for doc in db.movies.aggregate(director_pipeline):
        director_counts[doc["_id"]] = doc["count"]
    
    # Update cache
    _total_counts_cache["genres"] = genre_counts
    _total_counts_cache["actors"] = actor_counts
    _total_counts_cache["directors"] = director_counts
    _total_counts_cache["last_updated"] = datetime.now(timezone.utc)
    _total_counts_cache["total_movies"] = await db.movies.count_documents({})
    
    return _total_counts_cache

def calculate_proportion_score(user_count: int, total_available: int, total_user_movies: int, total_db_movies: int) -> float:
    """
    Calculate proportion-based score for fair comparison across categories.
    
    user_proportion = user_count / total_user_movies (what % of user's movies are in this category)
    available_proportion = total_available / total_db_movies (what % of all movies are in this category)
    
    Returns: user_proportion / available_proportion (values > 1 mean user watches more than average)
    """
    if total_available == 0 or total_user_movies == 0 or total_db_movies == 0:
        return 1.0
    
    user_proportion = user_count / total_user_movies
    available_proportion = total_available / total_db_movies
    
    # Ratio of user's preference vs what's available
    # > 1.0 means user prefers this more than average
    # < 1.0 means user watches less than what's available
    ratio = user_proportion / max(available_proportion, 0.001)
    
    return ratio

# ============ FRANCHISE HANDLING ============

def group_movies_by_franchise(movies_with_metadata: list) -> dict:
    """
    Group movies by franchise/collection.
    
    Returns dict with:
    - 'franchises': {franchise_id: [list of movie data]}
    - 'standalone': [list of non-franchise movies]
    """
    franchises = {}
    standalone = []
    
    for movie in movies_with_metadata:
        franchise = movie.get("franchise") or movie.get("meta", {}).get("franchise")
        if franchise and franchise.get("id"):
            fid = franchise["id"]
            fname = franchise.get("name", f"Franchise {fid}")
            if fid not in franchises:
                franchises[fid] = {
                    "name": fname,
                    "movies": []
                }
            franchises[fid]["movies"].append(movie)
        else:
            standalone.append(movie)
    
    return {
        "franchises": franchises,
        "standalone": standalone
    }

def aggregate_franchise_scores(franchise_movies: list) -> dict:
    """
    Aggregate scores for movies in a franchise to treat as single entity.
    
    Returns averaged metrics:
    - user_avg_rating: average of user ratings across franchise
    - preference: average preference signal
    - watch_count: counts as 1 (not N movies)
    - actors/directors/genres: deduplicated and averaged
    """
    if not franchise_movies:
        return {}
    
    # Average user ratings
    ratings = [m.get("user_avg", m.get("user_rating", 5)) for m in franchise_movies]
    avg_rating = sum(ratings) / len(ratings)
    
    # Average preference signals
    preferences = [m.get("preference", 0) for m in franchise_movies]
    avg_preference = sum(preferences) / len(preferences)
    
    # Collect unique actors/directors/genres (deduplicated)
    actors_seen = {}  # name -> best order position
    directors_seen = set()
    genres_seen = set()
    
    for m in franchise_movies:
        meta = m.get("meta", {})
        
        for actor in meta.get("cast", []):
            name = actor.get("name", "")
            if name:
                # Keep the best (lowest) order for this actor across franchise
                current_order = actors_seen.get(name, {}).get("order", 999)
                if actor.get("order", 999) < current_order:
                    actors_seen[name] = actor
        
        for director in meta.get("directors", []):
            name = director.get("name", "")
            if name:
                directors_seen.add(name)
        
        for genre in meta.get("genres", []):
            name = genre.get("name") if isinstance(genre, dict) else genre
            if name:
                genres_seen.add(name)
    
    return {
        "user_avg_rating": avg_rating,
        "avg_preference": avg_preference,
        "effective_count": 1,  # Counts as 1, not N
        "actual_movie_count": len(franchise_movies),
        "actors": actors_seen,
        "directors": list(directors_seen),
        "genres": list(genres_seen)
    }

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

# ============ FLICK SCORING ALGORITHM ============

def calculate_complexity_score(genres: List[str]) -> int:
    """Calculate movie complexity based on genres"""
    if not genres:
        return 5
    scores = [GENRE_COMPLEXITY.get(g, 5) for g in genres]
    return round(sum(scores) / len(scores))

def calculate_nostalgia_bonus(release_year: Optional[int], user_birth_year: int) -> float:
    """Add +2.0 if release_year is between user's birth_year + 12 and birth_year + 22"""
    if not release_year:
        return 0.0
    nostalgia_start = user_birth_year + 12
    nostalgia_end = user_birth_year + 22
    if nostalgia_start <= release_year <= nostalgia_end:
        return 2.0
    return 0.0

def calculate_complexity_penalty(genres: List[str], energy_level: int) -> float:
    """
    If energy is LOW (0-33), multiply score by 0.5 for complex genres, 1.5 for light genres
    If energy is HIGH (67-100), inverse penalty
    """
    if not genres:
        return 1.0
    
    genre_set = set(genres)
    has_low_energy = bool(genre_set & LOW_ENERGY_GENRES)
    has_high_energy = bool(genre_set & HIGH_ENERGY_GENRES)
    
    if energy_level < 33:  # LOW energy - user is exhausted
        if has_low_energy and not has_high_energy:
            return 0.5  # Penalize complex content
        if has_high_energy and not has_low_energy:
            return 1.5  # Boost light content
    elif energy_level > 67:  # HIGH energy - user is hyped
        if has_high_energy:
            return 1.3  # Boost action content
    
    return 1.0

async def calculate_rewatchability_multiplier(
    movie: dict,
    user_id: str,
    user_birth_year: int
) -> float:
    """
    Rs = (Days Since Last Watched / 365) × (User Rating + Nostalgia Bonus) / Complexity Penalty
    """
    tmdb_id = movie.get("id")
    
    # Check if in watch history
    watch_entry = await db.watch_history.find_one(
        {"user_id": user_id, "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    
    if not watch_entry:
        return 1.0
    
    last_watched = watch_entry.get("last_watched_date")
    if isinstance(last_watched, str):
        last_watched = datetime.fromisoformat(last_watched.replace('Z', '+00:00'))
    
    days_since = (datetime.now(timezone.utc) - last_watched).days
    user_rating = watch_entry.get("user_rating", 5)
    
    # Get release year
    release_date = movie.get("release_date", "")
    release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    
    # Get genres
    genre_ids = movie.get("genre_ids", [])
    genres = [GENRE_MAP.get(gid, "") for gid in genre_ids]
    
    nostalgia_bonus = calculate_nostalgia_bonus(release_year, user_birth_year)
    complexity = calculate_complexity_score(genres)
    
    # Avoid division by zero
    complexity_penalty = max(complexity / 5.0, 0.5)
    
    # Calculate multiplier
    Rs = ((days_since / 365.0) * (user_rating + nostalgia_bonus)) / complexity_penalty
    
    return max(Rs, 0.5)  # Minimum multiplier of 0.5

async def calculate_flick_score(
    movie: dict,
    user_id: str,
    user_birth_year: int,
    vibe_params: VibeParams
) -> dict:
    """
    Main scoring function:
    1. Base Score: TMDB average rating
    2. Rewatchability Multiplier
    3. Energy-based Complexity Penalty
    4. Mood adjustment
    """
    base_score = movie.get("vote_average", 5.0)
    
    # Get genres
    genre_ids = movie.get("genre_ids", [])
    genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
    
    # Apply complexity penalty based on energy
    complexity_penalty = calculate_complexity_penalty(genres, vibe_params.energy)
    
    # Calculate mood adjustment
    genre_set = set(genres)
    mood_adjustment = 1.0
    if vibe_params.mood < 33:  # Need a cry
        if genre_set & INTENSE_GENRES:
            mood_adjustment = 1.2
    elif vibe_params.mood > 67:  # Pure joy
        if genre_set & FEEL_GOOD_GENRES:
            mood_adjustment = 1.2
    
    # Get rewatchability multiplier if rewatches included
    rewatch_multiplier = 1.0
    if vibe_params.include_rewatches:
        rewatch_multiplier = await calculate_rewatchability_multiplier(
            movie, user_id, user_birth_year
        )
    
    # Nostalgia bonus
    release_date = movie.get("release_date", "")
    release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
    nostalgia_bonus = calculate_nostalgia_bonus(release_year, user_birth_year)
    
    # Final score calculation
    final_score = base_score * complexity_penalty * mood_adjustment * rewatch_multiplier
    final_score += nostalgia_bonus * 0.5  # Add nostalgia as bonus
    
    # Normalize to 0-100 match percentage
    match_percentage = min(round((final_score / 10.0) * 100), 100)
    
    # Generate vibe tag
    vibe_tag = generate_vibe_tag(genres, vibe_params, match_percentage)
    
    return {
        **movie,
        "match_percentage": match_percentage,
        "vibe_tag": vibe_tag,
        "genres": genres,
        "poster_url": get_image_url(movie.get("poster_path"), "w500"),
        "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
    }

def generate_vibe_tag(genres: List[str], vibe_params: VibeParams, match: int) -> str:
    """Generate a vibe tag based on movie and parameters"""
    genre_set = set(genres)
    
    if vibe_params.energy < 33:
        if match > 80:
            return "Perfect for a cozy night in"
        if genre_set & {"Comedy", "Animation"}:
            return "Light comfort viewing"
        return "Easy-going escapism"
    
    if vibe_params.energy > 67:
        if genre_set & {"Action", "Adventure"}:
            return "High-energy crowd pleaser"
        if genre_set & {"Thriller", "Horror"}:
            return "Edge-of-your-seat thriller"
        return "Get ready to be energized"
    
    if vibe_params.mood < 33:
        if genre_set & {"Drama", "Romance"}:
            return "Bring tissues"
        return "Emotionally resonant"
    
    if vibe_params.mood > 67:
        if genre_set & {"Comedy"}:
            return "Guaranteed laughs"
        return "Feel-good vibes"
    
    if match > 90:
        return "Your perfect match tonight"
    if match > 75:
        return "Highly recommended for you"
    
    return "Worth discovering"

# ============ API ENDPOINTS ============

@api_router.get("/")
async def root():
    return {"message": "Chef - Context-Aware Movie Recommendations"}

# ============ AUTH ENDPOINTS ============

@api_router.post("/auth/register")
async def register(data: UserRegister):
    """Register a new user"""
    # Check if email already exists
    existing = await db.auth_users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username exists
    existing_username = await db.auth_users.find_one({"username": data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": data.email.lower(),
        "username": data.username,
        "password_hash": hash_password(data.password),
        "birth_year": data.birth_year,
        "birth_date": data.birth_date,
        "avatar_url": None,
        "favorite_genres": [],
        "location_permission": None,
        "location": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.auth_users.insert_one(user_doc)
    
    # Create token
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email.lower(),
            "username": data.username,
            "birth_year": data.birth_year,
            "birth_date": data.birth_date,
            "avatar_url": None,
            "favorite_genres": [],
            "location_permission": None
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    """Login user"""
    user = await db.auth_users.find_one({"email": data.email.lower()})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email address")
    
    if not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Create token
    token = create_token(user["id"])
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "birth_year": user.get("birth_year", 1995),
            "birth_date": user.get("birth_date"),
            "avatar_url": user.get("avatar_url"),
            "favorite_genres": user.get("favorite_genres", []),
            "location_permission": user.get("location_permission"),
            "gender": user.get("gender"),
            "bio": user.get("bio"),
            "favorite_actors": user.get("favorite_actors", []),
            "favorite_movies": user.get("favorite_movies", []),
            "favorite_directors": user.get("favorite_directors", []),
            "letterboxd_connected": user.get("letterboxd_connected", False),
            "letterboxd_count": user.get("letterboxd_count", 0)
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current logged in user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

@api_router.put("/auth/profile")
async def update_profile(data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    update_data = {}
    if data.username is not None:
        # Check username not taken
        existing = await db.auth_users.find_one({
            "username": data.username, 
            "id": {"$ne": current_user["id"]}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = data.username
    
    if data.birth_year is not None:
        update_data["birth_year"] = data.birth_year
    
    if data.birth_date is not None:
        update_data["birth_date"] = data.birth_date
    
    if data.avatar_url is not None:
        update_data["avatar_url"] = data.avatar_url
    
    if data.favorite_genres is not None:
        update_data["favorite_genres"] = data.favorite_genres
    
    if data.gender is not None:
        update_data["gender"] = data.gender
    
    if data.bio is not None:
        update_data["bio"] = data.bio[:150]
    
    if data.favorite_actors is not None:
        update_data["favorite_actors"] = data.favorite_actors[:20]
    
    if data.favorite_movies is not None:
        update_data["favorite_movies"] = data.favorite_movies[:5]
    
    if data.streaming_services is not None:
        update_data["streaming_services"] = data.streaming_services
    
    if data.favorite_directors is not None:
        update_data["favorite_directors"] = data.favorite_directors[:20]
    
    if update_data:
        await db.auth_users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    user = await db.auth_users.find_one({"id": current_user["id"]}, {"_id": 0, "password_hash": 0})
    return user

@api_router.post("/auth/logout")
async def logout():
    """Logout (client should delete token)"""
    return {"message": "Logged out successfully"}

@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send password reset email"""
    email = data.email.lower().strip()
    user = await db.auth_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email address")
    
    # Generate a secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    # Store reset token in DB
    await db.password_resets.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "user_id": user["id"],
            "email": email,
            "token": reset_token,
            "expires_at": expires_at,
            "used": False
        }},
        upsert=True
    )
    
    # Build reset URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://diary-watch.preview.emergentagent.com")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Send email via Resend
    email_sent = False
    if RESEND_API_KEY:
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [email],
                "subject": "Chef - Reset Your Password",
                "html": f"""
                <div style="font-family: Georgia, serif; max-width: 480px; margin: 0 auto; padding: 40px 24px; background: #0a0a0a; color: #e5e5e5;">
                    <h1 style="font-size: 24px; color: #f5f0e8; margin-bottom: 16px;">Reset your password</h1>
                    <p style="font-size: 14px; line-height: 1.6; color: #999;">
                        We received a request to reset the password for your Chef account. Click the button below to set a new password.
                    </p>
                    <a href="{reset_url}" style="display: inline-block; margin: 24px 0; padding: 12px 32px; background: #2dd4bf22; border: 1px solid #2dd4bf44; color: #2dd4bf; text-decoration: none; border-radius: 9999px; font-size: 14px;">
                        Reset Password
                    </a>
                    <p style="font-size: 12px; color: #666; margin-top: 24px;">
                        This link expires in 1 hour. If you didn't request this, you can ignore this email.
                    </p>
                </div>
                """
            }
            await asyncio.to_thread(resend.Emails.send, params)
            email_sent = True
            logging.info(f"Password reset email sent to {email}")
        except Exception as e:
            logging.warning(f"Email send failed (will provide direct link): {e}")
    
    if email_sent:
        return {"message": "Password reset link sent to your email"}
    else:
        # Return reset URL directly when email can't be sent
        return {"message": "Reset link generated", "reset_url": reset_url}

@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using token from email"""
    record = await db.password_resets.find_one(
        {"token": data.token, "used": False},
        {"_id": 0}
    )
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    
    # Check expiry
    try:
        expires_str = record["expires_at"]
        # Handle timezone-aware and naive datetime strings
        expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
        # Make expires timezone-aware if it's naive
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid reset link")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.auth_users.update_one(
        {"id": record["user_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": data.token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password reset successfully. You can now log in."}

@api_router.put("/auth/location-permission")
async def update_location_permission(data: LocationPermissionUpdate, current_user: dict = Depends(get_current_user)):
    """Update user's location permission preference"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    update_data = {"location_permission": data.location_permission}
    if data.latitude is not None and data.longitude is not None:
        update_data["location"] = {
            "latitude": data.latitude,
            "longitude": data.longitude
        }
    
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Location permission updated", "location_permission": data.location_permission}

@api_router.post("/auth/upload-avatar")
async def upload_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload user avatar photo"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")
    
    # Read file (max 2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 2MB")
    
    # Save to uploads directory
    os.makedirs("/app/uploads/avatars", exist_ok=True)
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{current_user['id']}.{ext}"
    filepath = f"/app/uploads/avatars/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Store URL path in user record
    avatar_url = f"/api/uploads/avatars/{filename}"
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": {"avatar_url": avatar_url}}
    )
    
    return {"avatar_url": avatar_url}

def letterboxd_to_chef_rating(lb_rating: float, familiarity_boost: float = 0.0) -> float:
    """Non-linear Letterboxd (0-5) to Chef (0-10) conversion with familiarity adjustment.
    
    S-curve: compresses low ratings (1.5 and below), amplifies high ratings (3.5+).
    Midpoint (2.5/5) maps to 5.0/10 (same as linear).
    
    Familiarity boost: When user has watched more content from similar genres/directors/actors,
    the rating is adjusted slightly (up to ±0.5 points). Higher familiarity = more weight to user's taste.
    
    Args:
        lb_rating: Letterboxd rating (0-5 scale)
        familiarity_boost: Adjustment factor from -1.0 to 1.0 based on viewing history
    """
    if lb_rating is None or lb_rating <= 0:
        return 0.0
    lb_rating = min(lb_rating, 5.0)
    mid = 2.5
    if lb_rating <= mid:
        # Lower half: compress with exponent > 1
        normalized = lb_rating / mid  # 0.0 - 1.0
        chef = 5.0 * (normalized ** 1.4)
    else:
        # Upper half: stretch with exponent < 1
        normalized = (lb_rating - mid) / (5.0 - mid)  # 0.0 - 1.0
        chef = 5.0 + 5.0 * (normalized ** 0.6)
    
    # Apply familiarity adjustment (max ±0.5 points)
    # Higher familiarity amplifies deviations from neutral (5.0)
    if familiarity_boost != 0:
        deviation = chef - 5.0  # How far from neutral
        # Boost proportional to deviation and familiarity
        adjustment = deviation * familiarity_boost * 0.1  # Max 10% boost
        chef += adjustment
    
    return round(max(0.0, min(10.0, chef)), 1)


async def calculate_familiarity_scores(user_id: str) -> dict:
    """Calculate familiarity scores for genres, directors, and actors based on user's watch history.
    
    Returns dict with:
        - genres: {genre_name: count}
        - directors: {director_name: count}
        - actors: {actor_name: count}
        - max_genre_count, max_director_count, max_actor_count for normalization
    """
    # Get user's existing watch history
    history = await db.watch_history.find(
        {"user_id": user_id},
        {"_id": 0, "tmdb_id": 1}
    ).to_list(1000)
    
    if not history:
        return {
            "genres": {}, "directors": {}, "actors": {},
            "max_genre_count": 0, "max_director_count": 0, "max_actor_count": 0
        }
    
    tmdb_ids = [h["tmdb_id"] for h in history]
    
    # Get cached metadata for these movies
    cached_movies = await db.tmdb_cache.find(
        {"tmdb_id": {"$in": tmdb_ids}},
        {"_id": 0, "tmdb_id": 1, "genres": 1, "cast": 1, "directors": 1}
    ).to_list(1000)
    
    genre_counts = {}
    director_counts = {}
    actor_counts = {}
    
    for movie in cached_movies:
        # Count genres
        for genre in movie.get("genres", []):
            name = genre.get("name") if isinstance(genre, dict) else genre
            if name:
                genre_counts[name] = genre_counts.get(name, 0) + 1
        
        # Count directors
        for director in movie.get("directors", []):
            name = director.get("name") if isinstance(director, dict) else director
            if name:
                director_counts[name] = director_counts.get(name, 0) + 1
        
        # Count top actors (first 5)
        for actor in movie.get("cast", [])[:5]:
            name = actor.get("name") if isinstance(actor, dict) else actor
            if name:
                actor_counts[name] = actor_counts.get(name, 0) + 1
    
    return {
        "genres": genre_counts,
        "directors": director_counts,
        "actors": actor_counts,
        "max_genre_count": max(genre_counts.values()) if genre_counts else 0,
        "max_director_count": max(director_counts.values()) if director_counts else 0,
        "max_actor_count": max(actor_counts.values()) if actor_counts else 0
    }


def compute_familiarity_boost(movie_metadata: dict, familiarity_data: dict) -> float:
    """Compute familiarity boost for a movie based on user's viewing history.
    
    Returns a value between 0.0 and 1.0 representing how familiar the user is
    with this type of content (genres, directors, actors).
    """
    if not familiarity_data or not movie_metadata:
        return 0.0
    
    genre_scores = familiarity_data.get("genres", {})
    director_scores = familiarity_data.get("directors", {})
    actor_scores = familiarity_data.get("actors", {})
    
    max_genre = familiarity_data.get("max_genre_count", 1) or 1
    max_director = familiarity_data.get("max_director_count", 1) or 1
    max_actor = familiarity_data.get("max_actor_count", 1) or 1
    
    # Calculate genre familiarity (average of matching genres, normalized)
    movie_genres = movie_metadata.get("genres", [])
    genre_familiarity = 0.0
    if movie_genres:
        genre_matches = []
        for g in movie_genres:
            name = g.get("name") if isinstance(g, dict) else g
            if name and name in genre_scores:
                genre_matches.append(genre_scores[name] / max_genre)
        if genre_matches:
            genre_familiarity = sum(genre_matches) / len(genre_matches)
    
    # Calculate director familiarity
    movie_directors = movie_metadata.get("directors", [])
    director_familiarity = 0.0
    if movie_directors:
        dir_matches = []
        for d in movie_directors:
            name = d.get("name") if isinstance(d, dict) else d
            if name and name in director_scores:
                dir_matches.append(director_scores[name] / max_director)
        if dir_matches:
            director_familiarity = max(dir_matches)  # Use highest match for directors
    
    # Calculate actor familiarity (top 5 cast) WITH ACTOR IMPACT
    movie_cast = movie_metadata.get("cast", [])[:15]  # Get more cast for impact calc
    actor_familiarity = 0.0
    if movie_cast:
        # Get cast role counts
        cast_counts = movie_metadata.get("cast_counts", count_cast_by_role(movie_cast))
        num_leads = cast_counts.get("num_leads", 3)
        num_supporting = cast_counts.get("num_supporting", 7)
        total_cast = movie_metadata.get("total_cast", len(movie_cast))
        
        actor_weighted_matches = []
        for a in movie_cast:
            name = a.get("name") if isinstance(a, dict) else a
            if name and name in actor_scores:
                # Get actor's order for impact calculation
                actor_order = a.get("order", 99) if isinstance(a, dict) else 99
                actor_popularity = a.get("popularity", 0) if isinstance(a, dict) else 0
                
                # Calculate impact for this actor
                impact = calculate_actor_impact(
                    actor_order=actor_order,
                    total_cast=total_cast,
                    num_leads=num_leads,
                    num_supporting=num_supporting,
                    actor_filmography_count=actor_scores[name],  # Use count as proxy for experience
                    actor_popularity=actor_popularity
                )
                
                # Weight the familiarity score by actor impact
                base_familiarity = actor_scores[name] / max_actor
                weighted_familiarity = base_familiarity * impact["final_impact"]
                actor_weighted_matches.append(weighted_familiarity)
        
        if actor_weighted_matches:
            actor_familiarity = sum(actor_weighted_matches) / len(actor_weighted_matches)
    
    # Weighted combination: directors count most, then actors (now impact-weighted), then genres
    # Updated weights: director 35%, actors 35% (increased due to impact weighting), genre 30%
    total_familiarity = (
        director_familiarity * 0.35 +
        genre_familiarity * 0.30 +
        actor_familiarity * 0.35
    )
    
    return min(1.0, total_familiarity)


@api_router.post("/auth/import-letterboxd")
async def import_letterboxd(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Import Letterboxd data from CSV or ZIP file, populating diary and watchlist"""
    import csv
    import io
    import zipfile
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    is_zip = file.filename.endswith(".zip")
    is_csv = file.filename.endswith(".csv")
    if not is_zip and not is_csv:
        raise HTTPException(status_code=400, detail="Only .csv or .zip files are accepted")
    
    contents = await file.read()
    max_size = 10 * 1024 * 1024 if is_zip else 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"File size must be under {'10MB' if is_zip else '1MB'}")
    
    ratings_rows = []
    reviews_rows = []
    watchlist_rows = []
    legacy_entries = []
    
    def parse_csv_text(text):
        try:
            decoded = text.decode("utf-8-sig")
        except UnicodeDecodeError:
            decoded = text.decode("latin-1")
        return list(csv.DictReader(io.StringIO(decoded)))
    
    if is_zip:
        try:
            zf = zipfile.ZipFile(io.BytesIO(contents))
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file")
        
        for name in zf.namelist():
            basename = name.split("/")[-1].lower()
            # Only process root-level CSVs (not in deleted/orphaned subfolders)
            parts = [p for p in name.split("/") if p]
            is_root_csv = len(parts) == 1 or (len(parts) == 2 and parts[0].lower() not in ("deleted", "orphaned", "likes"))
            
            if basename == "ratings.csv" and is_root_csv:
                ratings_rows = parse_csv_text(zf.read(name))
            elif basename == "reviews.csv" and is_root_csv:
                reviews_rows = parse_csv_text(zf.read(name))
            elif basename == "watchlist.csv" and is_root_csv:
                watchlist_rows = parse_csv_text(zf.read(name))
        
        zf.close()
    else:
        # Legacy single CSV import
        rows = parse_csv_text(contents)
        for row in rows:
            entry = {}
            title = (row.get("Title") or row.get("Name") or "").strip()
            if not title:
                continue
            entry["title"] = title
            if row.get("Year"):
                try:
                    entry["year"] = int(row["Year"])
                except (ValueError, TypeError):
                    pass
            if row.get("Rating"):
                try:
                    r5 = float(row["Rating"])
                    entry["rating_5"] = r5
                    entry["rating_10"] = letterboxd_to_chef_rating(r5)
                except (ValueError, TypeError):
                    pass
            if row.get("WatchedDate"):
                entry["watched_date"] = row["WatchedDate"].strip()
            if row.get("Review"):
                entry["review"] = row["Review"].strip()[:500]
            if row.get("LetterboxdURI") or row.get("Letterboxd URI"):
                entry["letterboxd_uri"] = (row.get("LetterboxdURI") or row.get("Letterboxd URI") or "").strip()
            legacy_entries.append(entry)
    
    # --- Helper: search TMDB for a movie by name + year ---
    tmdb_api_key = os.environ.get("TMDB_API_KEY", "")
    tmdb_cache = {}
    tmdb_semaphore = asyncio.Semaphore(15)
    tmdb_client = httpx.AsyncClient(timeout=10)
    
    async def search_tmdb_movie(title: str, year: int = None) -> dict:
        cache_key = f"{title}|{year or ''}"
        if cache_key in tmdb_cache:
            return tmdb_cache[cache_key]
        
        async with tmdb_semaphore:
            # Re-check after acquiring semaphore (another task may have cached it)
            if cache_key in tmdb_cache:
                return tmdb_cache[cache_key]
            
            params = {"api_key": tmdb_api_key, "query": title}
            if year:
                params["year"] = year
            try:
                resp = await tmdb_client.get("https://api.themoviedb.org/3/search/movie", params=params)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        m = results[0]
                        result = {
                            "tmdb_id": m["id"],
                            "title": m.get("title", title),
                            "poster_path": m.get("poster_path"),
                            "release_date": m.get("release_date", ""),
                            "vote_average": m.get("vote_average", 0),
                        }
                        tmdb_cache[cache_key] = result
                        return result
                elif resp.status_code == 429:
                    await asyncio.sleep(1)
                    return await search_tmdb_movie(title, year)
            except Exception:
                pass
            tmdb_cache[cache_key] = None
            return None
    
    # --- Process ZIP data ---
    stats = {"diary_added": 0, "diary_updated": 0, "watchlist_added": 0, "skipped": 0, "total_processed": 0}
    
    if is_zip:
        # Calculate user's familiarity scores BEFORE processing new imports
        familiarity_data = await calculate_familiarity_scores(current_user["id"])
        
        # Pre-fetch all unique movies from TMDB in parallel
        unique_movies = {}
        for row in ratings_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            if name:
                year_val = int(year_str) if year_str.isdigit() else None
                unique_movies[f"{name}|{year_val or ''}"] = (name, year_val)
        for row in reviews_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            if name:
                year_val = int(year_str) if year_str.isdigit() else None
                unique_movies[f"{name}|{year_val or ''}"] = (name, year_val)
        for row in watchlist_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            if name:
                year_val = int(year_str) if year_str.isdigit() else None
                unique_movies[f"{name}|{year_val or ''}"] = (name, year_val)
        
        # Batch TMDB lookups concurrently
        if unique_movies:
            await asyncio.gather(*[
                search_tmdb_movie(title, year)
                for title, year in unique_movies.values()
            ])
        
        # Helper to get movie metadata for familiarity calculation
        async def get_movie_metadata(tmdb_id: int) -> dict:
            """Fetch movie metadata from cache or TMDB for familiarity calculation"""
            cached = await db.tmdb_cache.find_one({"tmdb_id": tmdb_id}, {"_id": 0})
            if cached and cached.get("genres"):
                return cached
            
            # Fetch from TMDB if not cached
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                        params={"api_key": TMDB_API_KEY, "append_to_response": "credits"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        genres = data.get("genres", [])
                        credits = data.get("credits", {})
                        cast = [{"name": c["name"], "profile_path": c.get("profile_path")} 
                                for c in credits.get("cast", [])[:10]]
                        directors = [{"name": c["name"], "profile_path": c.get("profile_path")} 
                                     for c in credits.get("crew", []) if c.get("job") == "Director"]
                        
                        metadata = {"tmdb_id": tmdb_id, "genres": genres, "cast": cast, "directors": directors}
                        
                        # Cache the metadata
                        await db.tmdb_cache.update_one(
                            {"tmdb_id": tmdb_id},
                            {"$set": metadata},
                            upsert=True
                        )
                        return metadata
            except Exception:
                pass
            return {}
        
        # Build review lookup: (name, year) -> review text
        review_map = {}
        for row in reviews_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            review_text = (row.get("Review") or "").strip()[:500]
            if name and review_text:
                year_val = int(year_str) if year_str.isdigit() else None
                review_map[(name.lower(), year_val)] = review_text
        
        # Process ratings.csv → Diary entries
        for row in ratings_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            rating_str = (row.get("Rating") or "").strip()
            date_str = (row.get("Date") or "").strip()
            if not name:
                continue
            
            stats["total_processed"] += 1
            year_val = int(year_str) if year_str.isdigit() else None
            
            # Search TMDB first to get tmdb_id for metadata lookup
            tmdb = await search_tmdb_movie(name, year_val)
            if not tmdb:
                stats["skipped"] += 1
                continue
            
            # Get movie metadata for familiarity calculation
            movie_metadata = await get_movie_metadata(tmdb["tmdb_id"])
            familiarity_boost = compute_familiarity_boost(movie_metadata, familiarity_data)
            
            # Convert 0-5 rating to 0-10 with familiarity adjustment
            try:
                rating_10 = letterboxd_to_chef_rating(float(rating_str), familiarity_boost) if rating_str else 7.0
            except ValueError:
                rating_10 = 7.0
            
            # Look up review
            comment = review_map.get((name.lower(), year_val), "")
            
            # Check if already in diary
            existing = await db.watch_history.find_one(
                {"user_id": current_user["id"], "tmdb_id": tmdb["tmdb_id"]},
                {"_id": 0}
            )
            
            watch_entry = {
                "id": str(uuid.uuid4()),
                "rating": rating_10,
                "date": date_str or "",
                "comment": comment,
                "source": "letterboxd"
            }
            
            if existing:
                # Add as a new watch only if not already imported from letterboxd
                has_lb = any(w.get("source") == "letterboxd" for w in existing.get("watches", []))
                if not has_lb:
                    watches = existing.get("watches", [])
                    watches.append(watch_entry)
                    summary = _sync_watch_summary(watches)
                    await db.watch_history.update_one(
                        {"user_id": current_user["id"], "tmdb_id": tmdb["tmdb_id"]},
                        {"$set": {"watches": watches, **summary}}
                    )
                    stats["diary_updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "tmdb_id": tmdb["tmdb_id"],
                    "user_rating": rating_10,
                    "watch_dates": [date_str] if date_str else [],
                    "last_watched_date": date_str or "",
                    "watch_count": 1,
                    "watches": [watch_entry],
                    "title": tmdb["title"],
                    "poster_path": tmdb["poster_path"],
                    "source": "letterboxd"
                }
                await db.watch_history.insert_one(doc)
                stats["diary_added"] += 1
        
        # Process reviews that DON'T have a rating (not already covered)
        rated_keys = set()
        for row in ratings_rows:
            n = (row.get("Name") or "").strip().lower()
            y = int(row["Year"]) if (row.get("Year") or "").strip().isdigit() else None
            if n:
                rated_keys.add((n, y))
        
        for row in reviews_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            rating_str = (row.get("Rating") or "").strip()
            review_text = (row.get("Review") or "").strip()[:500]
            date_str = (row.get("Date") or "").strip()
            if not name:
                continue
            
            year_val = int(year_str) if year_str.isdigit() else None
            if (name.lower(), year_val) in rated_keys:
                continue  # Already processed with rating
            
            stats["total_processed"] += 1
            
            tmdb = await search_tmdb_movie(name, year_val)
            if not tmdb:
                stats["skipped"] += 1
                continue
            
            # Get movie metadata for familiarity calculation
            movie_metadata = await get_movie_metadata(tmdb["tmdb_id"])
            familiarity_boost = compute_familiarity_boost(movie_metadata, familiarity_data)
            
            try:
                rating_10 = letterboxd_to_chef_rating(float(rating_str), familiarity_boost) if rating_str else 7.0
            except ValueError:
                rating_10 = 7.0
            
            existing = await db.watch_history.find_one(
                {"user_id": current_user["id"], "tmdb_id": tmdb["tmdb_id"]},
                {"_id": 0}
            )
            
            watch_entry = {
                "id": str(uuid.uuid4()),
                "rating": rating_10,
                "date": date_str or "",
                "comment": review_text,
                "source": "letterboxd"
            }
            
            if existing:
                has_lb = any(w.get("source") == "letterboxd" for w in existing.get("watches", []))
                if not has_lb:
                    watches = existing.get("watches", [])
                    watches.append(watch_entry)
                    summary = _sync_watch_summary(watches)
                    await db.watch_history.update_one(
                        {"user_id": current_user["id"], "tmdb_id": tmdb["tmdb_id"]},
                        {"$set": {"watches": watches, **summary}}
                    )
                    stats["diary_updated"] += 1
            else:
                doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "tmdb_id": tmdb["tmdb_id"],
                    "user_rating": rating_10,
                    "watch_dates": [date_str] if date_str else [],
                    "last_watched_date": date_str or "",
                    "watch_count": 1,
                    "watches": [watch_entry],
                    "title": tmdb["title"],
                    "poster_path": tmdb["poster_path"],
                    "source": "letterboxd"
                }
                await db.watch_history.insert_one(doc)
                stats["diary_added"] += 1
        
        # Process watchlist.csv → Watchlist
        for row in watchlist_rows:
            name = (row.get("Name") or "").strip()
            year_str = (row.get("Year") or "").strip()
            date_str = (row.get("Date") or "").strip()
            if not name:
                continue
            
            stats["total_processed"] += 1
            year_val = int(year_str) if year_str.isdigit() else None
            
            tmdb = await search_tmdb_movie(name, year_val)
            if not tmdb:
                stats["skipped"] += 1
                continue
            
            existing_wl = await db.watchlist.find_one(
                {"user_id": current_user["id"], "tmdb_id": tmdb["tmdb_id"]}
            )
            if existing_wl:
                stats["skipped"] += 1
                continue
            
            wl_doc = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "tmdb_id": tmdb["tmdb_id"],
                "title": tmdb["title"],
                "poster_path": tmdb["poster_path"],
                "release_date": tmdb.get("release_date", ""),
                "vote_average": tmdb.get("vote_average"),
                "genres": [],
                "added_at": datetime.now(timezone.utc).isoformat(),
                "source": "letterboxd"
            }
            await db.watchlist.insert_one(wl_doc)
            stats["watchlist_added"] += 1
        
        # Store import summary
        import_doc = {
            "user_id": current_user["id"],
            "ratings_count": len(ratings_rows),
            "reviews_count": len(reviews_rows),
            "watchlist_count": len(watchlist_rows),
            "stats": stats,
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "filename": file.filename
        }
        await db.letterboxd_imports.update_one(
            {"user_id": current_user["id"]},
            {"$set": import_doc},
            upsert=True
        )
        await db.auth_users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "letterboxd_connected": True,
                "letterboxd_count": stats["diary_added"] + stats["diary_updated"] + stats["watchlist_added"]
            }}
        )
        
        await tmdb_client.aclose()
        
        await _invalidate_insights_cache(current_user["id"])
        
        return {
            "message": f"Letterboxd import complete: {stats['diary_added']} diary entries, {stats['watchlist_added']} watchlist items",
            "stats": stats
        }
    
    # --- Legacy CSV import (no diary/watchlist population) ---
    if not legacy_entries:
        raise HTTPException(status_code=400, detail="No valid entries found in CSV")
    
    import_doc = {
        "user_id": current_user["id"],
        "entries": legacy_entries,
        "total_movies": len(legacy_entries),
        "rated_movies": sum(1 for e in legacy_entries if e.get("rating_5") or e.get("rating_10")),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "filename": file.filename
    }
    await db.letterboxd_imports.update_one(
        {"user_id": current_user["id"]},
        {"$set": import_doc},
        upsert=True
    )
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": {"letterboxd_connected": True, "letterboxd_count": len(legacy_entries)}}
    )
    
    return {
        "message": f"Successfully imported {len(legacy_entries)} movies from Letterboxd",
        "total": len(legacy_entries),
        "rated": sum(1 for e in legacy_entries if e.get("rating_5") or e.get("rating_10")),
    }

@api_router.get("/auth/letterboxd-data")
async def get_letterboxd_data(current_user: dict = Depends(get_current_user)):
    """Get user's imported Letterboxd data"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    data = await db.letterboxd_imports.find_one(
        {"user_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not data:
        return {"connected": False}
    
    return {
        "connected": True,
        "total_movies": data.get("total_movies", 0),
        "rated_movies": data.get("rated_movies", 0),
        "imported_at": data.get("imported_at"),
        "filename": data.get("filename"),
        "entries": data.get("entries", [])
    }

@api_router.get("/movies/search-tmdb")
async def search_tmdb_movies(query: str):
    """Search movies — local IMDB DB first, TMDB fallback for misses"""
    if not query or len(query) < 2:
        return {"results": []}
    
    # 1) Search local IMDB database (fast — indexed)
    local_results = await db.movies.find(
        {"$text": {"$search": query}},
        {"_id": 0, "score": {"$meta": "textScore"}}
    ).sort("score", {"$meta": "textScore"}).limit(8).to_list(8)
    
    results = []
    seen_titles = set()
    
    for m in local_results:
        key = f"{m['title'].lower()}|{m.get('year')}"
        if key in seen_titles:
            continue
        seen_titles.add(key)
        results.append({
            "id": m.get("imdb_id") or f"local_{m['title_lower']}_{m.get('year','')}",
            "title": m["title"],
            "year": str(m.get("year", "")),
            "poster_url": None,
            "rating": m.get("imdb_rating"),
            "source": "local"
        })
    
    # 2) Supplement with TMDB if not enough results
    if len(results) < 6:
        data = tmdb_request("/search/movie", {"query": query, "language": "en-US", "page": 1})
        if data:
            for movie in data.get("results", [])[:8]:
                title = movie.get("title", "")
                year = movie.get("release_date", "")[:4] if movie.get("release_date") else ""
                key = f"{title.lower()}|{year}"
                if key in seen_titles:
                    # Enrich existing local result with TMDB poster
                    for r in results:
                        if f"{r['title'].lower()}|{r['year']}" == key and not r.get("poster_url"):
                            r["poster_url"] = get_image_url(movie.get("poster_path"), "w185")
                            r["id"] = movie["id"]  # Use TMDB ID for detail lookups
                    continue
                seen_titles.add(key)
                results.append({
                    "id": movie["id"],
                    "title": title,
                    "year": year,
                    "poster_url": get_image_url(movie.get("poster_path"), "w185"),
                    "rating": round(movie.get("vote_average", 0), 1),
                    "source": "tmdb"
                })
    
    # 3) Backfill posters for local results that don't have them (quick TMDB lookup)
    for r in results:
        if not r.get("poster_url") and r.get("title"):
            data = tmdb_request("/search/movie", {"query": r["title"], "year": r.get("year"), "language": "en-US", "page": 1})
            if data and data.get("results"):
                tmdb_match = data["results"][0]
                r["poster_url"] = get_image_url(tmdb_match.get("poster_path"), "w185")
                if not isinstance(r["id"], int):
                    r["id"] = tmdb_match["id"]
    
    return {"results": results[:8]}

# User endpoints
@api_router.get("/user/profile")
async def get_user_profile():
    """Get mock user profile"""
    # Check if mock user exists
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    
    if not user:
        # Create mock user with birth year 1995
        mock_user = User(
            username="flick_user",
            birth_year=1995
        )
        doc = mock_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        user = doc
    
    # Remove _id if present
    if '_id' in user:
        del user['_id']
    
    return user

@api_router.get("/user/watch-history")
async def get_watch_history(current_user: dict = Depends(get_current_user)):
    """Get authenticated user's watch history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    history = await db.watch_history.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("last_watched_date", -1).to_list(500)
    
    # Auto-migrate: ensure every doc has a `watches` array
    for doc in history:
        if "watches" not in doc:
            watches = []
            watch_dates = doc.get("watch_dates", [])
            rating = doc.get("user_rating", 7.0)
            for wd in sorted(watch_dates):
                watches.append({
                    "id": str(uuid.uuid4()),
                    "rating": rating,
                    "date": wd,
                    "comment": ""
                })
            if not watches and doc.get("last_watched_date"):
                watches.append({
                    "id": str(uuid.uuid4()),
                    "rating": rating,
                    "date": doc.get("last_watched_date", ""),
                    "comment": ""
                })
            doc["watches"] = watches
            # Persist migration
            await db.watch_history.update_one(
                {"user_id": current_user["id"], "tmdb_id": doc["tmdb_id"]},
                {"$set": {"watches": watches}}
            )
    
    return history

@api_router.post("/user/watch-history")
async def add_to_watch_history(item: WatchHistoryCreate, current_user: dict = Depends(get_current_user)):
    """Add movie to authenticated user's watch history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    watched_date = item.watched_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    watch_entry = {
        "id": str(uuid.uuid4()),
        "rating": item.user_rating,
        "date": watched_date,
        "comment": ""
    }
    
    # Check if already in history
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
        {"_id": 0}
    )
    
    if existing:
        watches = existing.get("watches", [])
        watches.append(watch_entry)
        watch_dates = [w["date"] for w in watches]
        watch_dates_sorted = sorted(watch_dates, reverse=True)
        
        await db.watch_history.update_one(
            {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
            {
                "$set": {
                    "user_rating": item.user_rating,
                    "last_watched_date": watch_dates_sorted[0],
                    "watch_dates": watch_dates_sorted,
                    "watch_count": len(watches),
                    "watches": watches,
                    "title": item.title or existing.get("title", ""),
                    "poster_path": item.poster_path or existing.get("poster_path")
                }
            }
        )
        updated = await db.watch_history.find_one(
            {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
            {"_id": 0}
        )
        await _invalidate_insights_cache(current_user["id"])
        return updated
    
    # Create new entry
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "tmdb_id": item.tmdb_id,
        "user_rating": item.user_rating,
        "watch_dates": [watched_date],
        "last_watched_date": watched_date,
        "watch_count": 1,
        "watches": [watch_entry],
        "title": item.title,
        "poster_path": item.poster_path
    }
    await db.watch_history.insert_one(doc)
    doc.pop("_id", None)
    await _invalidate_insights_cache(current_user["id"])
    return doc

@api_router.put("/user/watch-history/{tmdb_id}")
async def update_watch_history(tmdb_id: int, data: WatchHistoryUpdate, current_user: dict = Depends(get_current_user)):
    """Update rating or add a watch date for a movie in history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    update = {}
    if data.user_rating is not None:
        update["user_rating"] = data.user_rating
    
    if data.watched_date:
        watch_dates = existing.get("watch_dates", [])
        if data.watched_date not in watch_dates:
            watch_dates.append(data.watched_date)
            watch_dates.sort(reverse=True)
            update["watch_dates"] = watch_dates
            update["last_watched_date"] = watch_dates[0]
            update["watch_count"] = len(watch_dates)
    
    if update:
        await db.watch_history.update_one(
            {"user_id": current_user["id"], "tmdb_id": tmdb_id},
            {"$set": update}
        )
    
    updated = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    return updated

@api_router.delete("/user/watch-history/{tmdb_id}")
async def remove_from_watch_history(tmdb_id: int, current_user: dict = Depends(get_current_user)):
    """Remove movie from authenticated user's watch history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.watch_history.delete_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    await _invalidate_insights_cache(current_user["id"])
    return {"message": "Removed from watch history"}

@api_router.delete("/user/watch-history")
async def clear_all_watch_history(current_user: dict = Depends(get_current_user)):
    """Clear all movies from authenticated user's watch history (diary)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.watch_history.delete_many({"user_id": current_user["id"]})
    await _invalidate_insights_cache(current_user["id"])
    
    return {"message": f"Cleared {result.deleted_count} movies from diary", "deleted_count": result.deleted_count}

# ============ INDIVIDUAL WATCH ENTRY ENDPOINTS ============

def _sync_watch_summary(watches: list) -> dict:
    """Recompute summary fields from watches array"""
    if not watches:
        return {"user_rating": 0, "last_watched_date": "", "watch_dates": [], "watch_count": 0}
    dates = sorted([w["date"] for w in watches if w.get("date")], reverse=True)
    latest_watch = max(watches, key=lambda w: w.get("date", ""))
    return {
        "user_rating": latest_watch.get("rating", 0),
        "last_watched_date": dates[0] if dates else "",
        "watch_dates": dates,
        "watch_count": len(watches),
    }

@api_router.post("/user/watch-history/{tmdb_id}/watches")
async def add_watch_entry(tmdb_id: int, entry: WatchEntryCreate, current_user: dict = Depends(get_current_user)):
    """Add a new watch entry to an existing movie in history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    watch_entry = {
        "id": str(uuid.uuid4()),
        "rating": entry.rating,
        "date": entry.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "comment": (entry.comment or "")[:500]
    }
    
    watches = existing.get("watches", [])
    watches.append(watch_entry)
    summary = _sync_watch_summary(watches)
    
    await db.watch_history.update_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"$set": {"watches": watches, **summary}}
    )
    
    updated = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    return updated

@api_router.put("/user/watch-history/{tmdb_id}/watches/{watch_id}")
async def update_watch_entry(tmdb_id: int, watch_id: str, entry: WatchEntryUpdate, current_user: dict = Depends(get_current_user)):
    """Edit a single watch entry"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    watches = existing.get("watches", [])
    found = False
    for w in watches:
        if w["id"] == watch_id:
            if entry.rating is not None:
                w["rating"] = entry.rating
            if entry.date is not None:
                w["date"] = entry.date
            if entry.comment is not None:
                w["comment"] = entry.comment[:500]
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="Watch entry not found")
    
    summary = _sync_watch_summary(watches)
    
    await db.watch_history.update_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"$set": {"watches": watches, **summary}}
    )
    
    updated = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    await _invalidate_insights_cache(current_user["id"])
    return updated

@api_router.delete("/user/watch-history/{tmdb_id}/watches/{watch_id}")
async def delete_watch_entry(tmdb_id: int, watch_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a single watch entry. If last entry, removes the movie from history."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    watches = existing.get("watches", [])
    new_watches = [w for w in watches if w["id"] != watch_id]
    
    if len(new_watches) == len(watches):
        raise HTTPException(status_code=404, detail="Watch entry not found")
    
    if not new_watches:
        await db.watch_history.delete_one(
            {"user_id": current_user["id"], "tmdb_id": tmdb_id}
        )
        await _invalidate_insights_cache(current_user["id"])
        return {"message": "Movie removed from history (last watch deleted)", "removed": True}
    
    summary = _sync_watch_summary(new_watches)
    
    await db.watch_history.update_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"$set": {"watches": new_watches, **summary}}
    )
    
    updated = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    await _invalidate_insights_cache(current_user["id"])
    return updated

# ============ PROFILE INSIGHTS (CACHED) ============

async def _get_movie_metadata(tmdb_ids: list) -> dict:
    """Get genres/cast/crew for movies, using MongoDB cache first, TMDB API for misses.
    Now includes cast order and popularity for actor impact calculation."""
    result = {}
    
    # Batch read from cache
    cached = await db.movie_metadata.find(
        {"tmdb_id": {"$in": tmdb_ids}},
        {"_id": 0}
    ).to_list(len(tmdb_ids))
    for doc in cached:
        result[doc["tmdb_id"]] = doc
    
    # Find cache misses
    missing = [tid for tid in tmdb_ids if tid not in result]
    if not missing:
        return result
    
    # Fetch from TMDB concurrently
    tmdb_api_key = os.environ.get("TMDB_API_KEY", "")
    sem = asyncio.Semaphore(15)
    
    async def fetch_and_cache(tmdb_id):
        async with sem:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    dr, cr = await asyncio.gather(
                        client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", params={"api_key": tmdb_api_key}),
                        client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits", params={"api_key": tmdb_api_key}),
                    )
                details = dr.json() if dr.status_code == 200 else {}
                credits = cr.json() if cr.status_code == 200 else {}
                
                genres = [{"id": g["id"], "name": g["name"]} for g in details.get("genres", [])]
                
                # Extract franchise/collection info
                collection = details.get("belongs_to_collection")
                franchise_info = None
                if collection:
                    franchise_info = {
                        "id": collection.get("id"),
                        "name": collection.get("name")
                    }
                
                # Enhanced cast data with order and popularity for actor impact
                raw_cast = credits.get("cast") or []
                cast = [
                    {
                        "name": a["name"], 
                        "profile_path": a.get("profile_path"),
                        "order": a.get("order", i),  # Billing order
                        "popularity": a.get("popularity", 0),  # TMDB popularity
                        "character": a.get("character", ""),
                    } 
                    for i, a in enumerate(raw_cast[:15])  # Store top 15 for analysis
                ]
                
                directors = [
                    {
                        "name": c["name"], 
                        "profile_path": c.get("profile_path"),
                        "popularity": c.get("popularity", 0)
                    } 
                    for c in (credits.get("crew") or []) if c.get("job") == "Director"
                ]
                
                # Count cast by role for this movie
                cast_role_counts = count_cast_by_role(cast)
                
                doc = {
                    "tmdb_id": tmdb_id, 
                    "genres": genres, 
                    "cast": cast, 
                    "directors": directors,
                    "cast_counts": cast_role_counts,
                    "total_cast": len(raw_cast),
                    "franchise": franchise_info  # Add franchise data
                }
                await db.movie_metadata.update_one(
                    {"tmdb_id": tmdb_id}, {"$set": doc}, upsert=True
                )
                return doc
            except Exception:
                return {"tmdb_id": tmdb_id, "genres": [], "cast": [], "directors": [], "cast_counts": {}, "total_cast": 0, "franchise": None}
    
    fetched = await asyncio.gather(*[fetch_and_cache(tid) for tid in missing])
    for doc in fetched:
        result[doc["tmdb_id"]] = doc
    
    return result


async def _invalidate_insights_cache(user_id: str):
    """Call this whenever diary changes to bust the insights cache."""
    await db.profile_insights_cache.delete_one({"user_id": user_id})


@api_router.get("/user/profile-insights")
async def get_profile_insights(current_user: dict = Depends(get_current_user)):
    """
    Return cached top 5 genres, actors, directors with:
    - Proportion-based scoring (normalized by availability)
    - Franchise deduplication (MCU movies count as 1 entity)
    - Actor impact weighting (lead > supporting > background)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check user-level cache first
    cached = await db.profile_insights_cache.find_one(
        {"user_id": current_user["id"]}, {"_id": 0}
    )
    if cached:
        return {"genres": cached["genres"], "actors": cached["actors"], "directors": cached["directors"]}
    
    # Get diary entries
    history = await db.watch_history.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "tmdb_id": 1, "user_rating": 1, "watch_count": 1, "watches": 1, "title": 1}
    ).to_list(500)
    
    if not history:
        return {"genres": [], "actors": [], "directors": []}
    
    # Get metadata for all movies (includes franchise info)
    tmdb_ids = [h["tmdb_id"] for h in history]
    metadata = await _get_movie_metadata(tmdb_ids)
    
    # Get total counts for proportion calculation
    total_counts = await get_total_counts()
    total_db_movies = total_counts.get("total_movies", 1) or 1
    total_user_movies = len(history)
    
    # Fetch IMDB data for all movies at once
    local_movies = {}
    for tmdb_id, title in title_map.items():
        if title:
            local = await db.movies.find_one(
                {"title_lower": title.lower()},
                {"_id": 0, "imdb_rating": 1, "imdb_votes": 1}
            )
            if local:
                local_movies[tmdb_id] = local
    
    # Compute global mean IMDB rating and Bayesian prior
    # Using m=1000 as minimum votes for full weight (Bayesian shrinkage)
    GLOBAL_MEAN = 6.5  # Approximate IMDB global mean
    BAYESIAN_M = 1000  # Minimum votes for full confidence
    
    def bayesian_expected(imdb_rating, imdb_votes):
        """Shrink IMDB rating toward global mean for movies with few votes."""
        if not imdb_rating or not imdb_votes:
            return GLOBAL_MEAN
        v = max(imdb_votes, 1)
        return (v * imdb_rating + BAYESIAN_M * GLOBAL_MEAN) / (v + BAYESIAN_M)
    
    # Score computation — preference signal: user_rating - bayesian_expected
    genre_scores = {}
    actor_scores = {}
    director_scores = {}
    
    # Track actor filmography for experience calculation
    actor_filmography = {}
    
    for h in history:
        watches = h.get("watches", [])
        user_avg = (sum(w.get("rating", 0) for w in watches) / len(watches)) if watches else h.get("user_rating", 5.0)
        watch_count = h.get("watch_count", 1) or 1
        
        # Get expected rating (Bayesian-adjusted IMDB rating)
        local = local_movies.get(h["tmdb_id"])
        expected = bayesian_expected(
            local.get("imdb_rating") if local else None,
            local.get("imdb_votes") if local else None
        )
        
        # Preference signal: how much the user liked it vs expected
        preference = user_avg - expected
        
        # Weight: preference signal boosted by rewatch frequency
        # A positive preference means the user liked it more than average
        # Multiply by a base factor to keep scores meaningful even for neutral preferences
        rewatch_boost = 1 + 0.15 * (watch_count - 1)
        base_weight = (preference + 3.0) * rewatch_boost  # +3 shift so slightly-liked movies still contribute positively
        
        meta = metadata.get(h["tmdb_id"], {})
        
        for genre in meta.get("genres", []):
            name = genre["name"]
            if name not in genre_scores:
                genre_scores[name] = {"total_weight": 0, "count": 0, "total_pref": 0, "total_expected": 0}
            genre_scores[name]["total_weight"] += base_weight
            genre_scores[name]["count"] += 1
            genre_scores[name]["total_pref"] += preference
            genre_scores[name]["total_expected"] += expected
        
        # Get cast role counts for actor impact calculation
        cast_counts = meta.get("cast_counts", {})
        num_leads = cast_counts.get("num_leads", 3)
        num_supporting = cast_counts.get("num_supporting", 7)
        total_cast = meta.get("total_cast", 15)
        
        # Process actors with impact-weighted scoring
        for actor in meta.get("cast", []):
            name = actor.get("name", "")
            if not name:
                continue
            
            # Track filmography count for this actor
            actor_filmography[name] = actor_filmography.get(name, 0) + 1
            
            # Calculate actor's impact on this movie
            actor_order = actor.get("order", 99)
            actor_popularity = actor.get("popularity", 0)
            
            impact_data = calculate_actor_impact(
                actor_order=actor_order,
                total_cast=total_cast,
                num_leads=num_leads,
                num_supporting=num_supporting,
                actor_filmography_count=actor_filmography[name],
                actor_popularity=actor_popularity
            )
            
            # Apply actor impact to weight
            actor_weight = base_weight * impact_data["final_impact"]
            
            if name not in actor_scores:
                actor_scores[name] = {
                    "total_weight": 0, 
                    "count": 0, 
                    "total_pref": 0, 
                    "total_expected": 0, 
                    "profile_path": actor.get("profile_path"),
                    "total_impact": 0,
                    "roles": {"lead": 0, "supporting": 0, "background": 0},
                    "avg_popularity": 0,
                    "filmography_in_diary": 0
                }
            
            actor_scores[name]["total_weight"] += actor_weight
            actor_scores[name]["count"] += 1
            actor_scores[name]["total_pref"] += preference
            actor_scores[name]["total_expected"] += expected
            actor_scores[name]["total_impact"] += impact_data["final_impact"]
            actor_scores[name]["roles"][impact_data["role"]] += 1
            actor_scores[name]["avg_popularity"] += actor_popularity
            actor_scores[name]["filmography_in_diary"] = actor_filmography[name]
        
        for director in meta.get("directors", []):
            name = director.get("name", "")
            if not name:
                continue
            if name not in director_scores:
                director_scores[name] = {"total_weight": 0, "count": 0, "total_pref": 0, "total_expected": 0, "profile_path": director.get("profile_path")}
            director_scores[name]["total_weight"] += base_weight
            director_scores[name]["count"] += 1
            director_scores[name]["total_pref"] += preference
            director_scores[name]["total_expected"] += expected
    
    def rank_genres(scores_dict, limit=5):
        ranked = sorted(scores_dict.items(), key=lambda x: x[1]["total_weight"], reverse=True)
        return [
            {
                "name": name,
                "score": round(data["total_weight"], 1),
                "count": data["count"],
                "avg_preference": round(data["total_pref"] / data["count"], 1) if data["count"] else 0,
                "avg_expected": round(data["total_expected"] / data["count"], 1) if data["count"] else 0,
            }
            for name, data in ranked[:limit]
        ]
    
    def rank_actors(scores_dict, limit=5):
        """Rank actors using impact-weighted scores."""
        ranked = sorted(scores_dict.items(), key=lambda x: x[1]["total_weight"], reverse=True)
        return [
            {
                "name": name,
                "score": round(data["total_weight"], 1),
                "count": data["count"],
                "avg_preference": round(data["total_pref"] / data["count"], 1) if data["count"] else 0,
                "avg_expected": round(data["total_expected"] / data["count"], 1) if data["count"] else 0,
                "profile_path": data.get("profile_path"),
                "avg_impact": round(data["total_impact"] / data["count"], 3) if data["count"] else 0,
                "roles": data.get("roles", {}),
                "primary_role": max(data.get("roles", {"lead": 0}), key=data.get("roles", {"lead": 0}).get),
                "filmography_count": data.get("filmography_in_diary", 0),
                "avg_popularity": round(data["avg_popularity"] / data["count"], 1) if data["count"] else 0,
            }
            for name, data in ranked[:limit]
        ]
    
    def rank_directors(scores_dict, limit=5):
        ranked = sorted(scores_dict.items(), key=lambda x: x[1]["total_weight"], reverse=True)
        return [
            {
                "name": name,
                "score": round(data["total_weight"], 1),
                "count": data["count"],
                "avg_preference": round(data["total_pref"] / data["count"], 1) if data["count"] else 0,
                "avg_expected": round(data["total_expected"] / data["count"], 1) if data["count"] else 0,
                "profile_path": data.get("profile_path"),
            }
            for name, data in ranked[:limit]
        ]
    
    result = {
        "genres": rank_genres_with_proportion(genre_scores),
        "actors": rank_actors_with_proportion(actor_scores),
        "directors": rank_directors_with_proportion(director_scores),
        "stats": {
            "total_movies_watched": total_user_movies,
            "effective_entries": effective_total,
            "franchises_watched": len(grouped["franchises"]),
            "standalone_movies": len(grouped["standalone"])
        }
    }
    
    # Cache the result
    await db.profile_insights_cache.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"user_id": current_user["id"], **result}},
        upsert=True
    )
    
    return result

# ============ WATCHLIST ENDPOINTS ============

@api_router.get("/user/watchlist")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    """Get authenticated user's watchlist"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    items = await db.watchlist.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("added_at", -1).to_list(500)
    
    return items

@api_router.post("/user/watchlist")
async def add_to_watchlist(item: WatchlistAdd, current_user: dict = Depends(get_current_user)):
    """Add movie to authenticated user's watchlist"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing = await db.watchlist.find_one(
        {"user_id": current_user["id"], "tmdb_id": item.tmdb_id}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "tmdb_id": item.tmdb_id,
        "title": item.title,
        "poster_path": item.poster_path,
        "release_date": item.release_date,
        "vote_average": item.vote_average,
        "genres": item.genres or [],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    await db.watchlist.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.delete("/user/watchlist/{tmdb_id}")
async def remove_from_watchlist(tmdb_id: int, current_user: dict = Depends(get_current_user)):
    """Remove movie from authenticated user's watchlist"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.watchlist.delete_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Movie not in watchlist")
    return {"message": "Removed from watchlist"}

@api_router.delete("/user/watchlist")
async def clear_all_watchlist(current_user: dict = Depends(get_current_user)):
    """Clear all movies from authenticated user's watchlist"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.watchlist.delete_many({"user_id": current_user["id"]})
    
    return {"message": f"Cleared {result.deleted_count} movies from watchlist", "deleted_count": result.deleted_count}

@api_router.get("/user/watchlist/check/{tmdb_id}")
async def check_watchlist(tmdb_id: int, current_user: dict = Depends(get_current_user)):
    """Check if a movie is in the user's watchlist"""
    if not current_user:
        return {"in_watchlist": False}
    
    existing = await db.watchlist.find_one(
        {"user_id": current_user["id"], "tmdb_id": tmdb_id},
        {"_id": 0}
    )
    return {"in_watchlist": existing is not None}

# ============ CURATED FOR YOU - PERSONALIZED RECOMMENDATIONS ============

@api_router.get("/movies/curated-for-you")
async def get_curated_for_you(current_user: dict = Depends(get_current_user)):
    """
    Generate personalized movie recommendations based on user's:
    - Watch history (ratings, watch count, recency)
    - Favorite genres/actors/directors from profile insights
    - Watchlist (movies user wants to watch)
    
    Returns top 20 movies ranked by curated score.
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # If user not logged in, return trending movies as fallback
    if not current_user:
        data = tmdb_request("/trending/movie/week")
        if not data:
            raise HTTPException(status_code=500, detail="Failed to fetch movies")
        return {"results": data.get("results", [])[:20], "personalized": False}
    
    user_id = current_user["id"]
    
    # 1. Get user's watch history with ratings and watch data
    watch_history = await db.watch_history.find(
        {"user_id": user_id},
        {"_id": 0, "tmdb_id": 1, "user_rating": 1, "watch_count": 1, "watches": 1, "last_watched_date": 1}
    ).to_list(500)
    
    # 2. Get user's watchlist
    watchlist = await db.watchlist.find(
        {"user_id": user_id},
        {"_id": 0, "tmdb_id": 1}
    ).to_list(200)
    watchlist_ids = set(w["tmdb_id"] for w in watchlist)
    watched_ids = set(h["tmdb_id"] for h in watch_history)
    
    # 3. Calculate genre/actor/director preferences from watch history
    genre_scores = {}
    director_scores = {}
    actor_scores = {}
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    for h in watch_history:
        tmdb_id = h["tmdb_id"]
        rating = h.get("user_rating", 5.0)
        watch_count = h.get("watch_count", 1) or 1
        
        # Calculate recency boost (more recent = higher weight)
        last_watch = h.get("last_watched_date", "")
        recency_boost = 1.0
        if last_watch:
            try:
                watch_date = datetime.fromisoformat(last_watch.replace("Z", "+00:00")) if "T" in last_watch else datetime.strptime(last_watch, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_ago = (now - watch_date).days
                # Exponential decay: recent watches get more weight
                recency_boost = max(0.5, 1.0 - (days_ago / 365) * 0.5)  # 0.5 to 1.0
            except:
                recency_boost = 0.75
        
        # Combined preference weight: rating * rewatch bonus * recency
        # Higher ratings (6+) contribute positively, lower ratings contribute less
        rating_factor = (rating - 5.0) / 5.0  # -1.0 to 1.0
        rewatch_bonus = 1.0 + 0.2 * (watch_count - 1)  # 1.0, 1.2, 1.4, etc.
        preference_weight = (1.0 + rating_factor) * rewatch_bonus * recency_boost
        
        # Get movie metadata for genre/cast/director info
        cached = await db.tmdb_cache.find_one({"tmdb_id": tmdb_id}, {"_id": 0})
        if cached:
            for genre in cached.get("genres", []):
                name = genre.get("name") if isinstance(genre, dict) else genre
                if name:
                    genre_scores[name] = genre_scores.get(name, 0) + preference_weight
            
            for director in cached.get("directors", []):
                name = director.get("name") if isinstance(director, dict) else director
                if name:
                    director_scores[name] = director_scores.get(name, 0) + preference_weight
            
            for actor in cached.get("cast", [])[:5]:
                name = actor.get("name") if isinstance(actor, dict) else actor
                if name:
                    actor_scores[name] = actor_scores.get(name, 0) + preference_weight * 0.5  # Actors weighted less
    
    # Normalize scores
    max_genre = max(genre_scores.values()) if genre_scores else 1
    max_director = max(director_scores.values()) if director_scores else 1
    max_actor = max(actor_scores.values()) if actor_scores else 1
    
    genre_prefs = {k: v / max_genre for k, v in genre_scores.items()}
    director_prefs = {k: v / max_director for k, v in director_scores.items()}
    actor_prefs = {k: v / max_actor for k, v in actor_scores.items()}
    
    # 4. Get candidate movies from multiple sources
    candidate_movies = []
    seen_ids = set()
    
    # Source 1: Watchlist movies (highest priority - user explicitly wants these)
    for w in watchlist[:30]:
        if w["tmdb_id"] not in seen_ids:
            movie_data = tmdb_request(f"/movie/{w['tmdb_id']}", {"append_to_response": "credits"})
            if movie_data:
                candidate_movies.append({"source": "watchlist", "data": movie_data})
                seen_ids.add(w["tmdb_id"])
    
    # Source 2: Similar to highly-rated movies in history
    top_rated = sorted(watch_history, key=lambda x: x.get("user_rating", 0), reverse=True)[:5]
    for h in top_rated:
        similar = tmdb_request(f"/movie/{h['tmdb_id']}/similar")
        if similar:
            for m in similar.get("results", [])[:5]:
                if m["id"] not in seen_ids and m["id"] not in watched_ids:
                    candidate_movies.append({"source": "similar", "data": m})
                    seen_ids.add(m["id"])
    
    # Source 3: Discover movies in favorite genres
    top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    genre_ids = [str(gid) for gname, _ in top_genres for gid, name in GENRE_MAP.items() if name == gname]
    if genre_ids:
        discover_data = tmdb_request("/discover/movie", {
            "sort_by": "vote_average.desc",
            "vote_count.gte": 200,
            "vote_average.gte": 7.0,
            "with_genres": ",".join(genre_ids[:2])
        })
        if discover_data:
            for m in discover_data.get("results", [])[:15]:
                if m["id"] not in seen_ids and m["id"] not in watched_ids:
                    candidate_movies.append({"source": "genre_match", "data": m})
                    seen_ids.add(m["id"])
    
    # Source 4: Trending (for diversity)
    trending = tmdb_request("/trending/movie/week")
    if trending:
        for m in trending.get("results", [])[:10]:
            if m["id"] not in seen_ids and m["id"] not in watched_ids:
                candidate_movies.append({"source": "trending", "data": m})
                seen_ids.add(m["id"])
    
    # 5. Calculate curated score for each candidate
    scored_movies = []
    
    for candidate in candidate_movies:
        movie = candidate["data"]
        source = candidate["source"]
        tmdb_id = movie.get("id")
        
        # Base score
        curated_score = 0.0
        
        # Watchlist boost (major boost - user explicitly wants this)
        if source == "watchlist" or tmdb_id in watchlist_ids:
            curated_score += 30.0
        
        # Genre match scoring
        movie_genres = movie.get("genres", []) or []
        if not movie_genres and movie.get("genre_ids"):
            movie_genres = [{"name": GENRE_MAP.get(gid, "")} for gid in movie.get("genre_ids", [])]
        
        genre_match = 0.0
        for g in movie_genres:
            gname = g.get("name") if isinstance(g, dict) else GENRE_MAP.get(g, "")
            if gname in genre_prefs:
                genre_match += genre_prefs[gname]
        if movie_genres:
            genre_match /= len(movie_genres)
        curated_score += genre_match * 25.0  # Max 25 points for genre match
        
        # Director match scoring
        credits = movie.get("credits", {})
        directors = [c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"]
        director_match = 0.0
        for d in directors:
            if d in director_prefs:
                director_match = max(director_match, director_prefs[d])
        curated_score += director_match * 20.0  # Max 20 points for director match
        
        # Actor match scoring
        cast = credits.get("cast", [])[:5]
        actor_match = 0.0
        for a in cast:
            aname = a.get("name", "")
            if aname in actor_prefs:
                actor_match += actor_prefs[aname]
        if cast:
            actor_match /= len(cast)
        curated_score += actor_match * 15.0  # Max 15 points for actor match
        
        # Quality bonus (TMDB rating)
        vote_avg = movie.get("vote_average", 0)
        vote_count = movie.get("vote_count", 0)
        if vote_count > 100 and vote_avg >= 6.0:
            quality_bonus = (vote_avg - 6.0) / 4.0 * 10.0  # Max 10 points for 10-rated movies
            curated_score += quality_bonus
        
        # Source bonus
        if source == "similar":
            curated_score += 5.0  # Bonus for being similar to liked movies
        
        scored_movies.append({
            "id": tmdb_id,
            "title": movie.get("title", ""),
            "poster_path": movie.get("poster_path"),
            "backdrop_path": movie.get("backdrop_path"),
            "overview": movie.get("overview", ""),
            "release_date": movie.get("release_date", ""),
            "vote_average": vote_avg,
            "vote_count": vote_count,
            "genre_ids": movie.get("genre_ids", []),
            "genres": [g.get("name") if isinstance(g, dict) else GENRE_MAP.get(g, str(g)) for g in movie_genres],
            "curated_score": round(curated_score, 1),
            "in_watchlist": tmdb_id in watchlist_ids,
            "match_reason": _get_match_reason(source, genre_match, director_match, actor_match, tmdb_id in watchlist_ids)
        })
    
    # Sort by curated score (highest first)
    scored_movies.sort(key=lambda x: x["curated_score"], reverse=True)
    
    # Return top 20
    return {
        "results": scored_movies[:20],
        "personalized": True,
        "total_candidates": len(candidate_movies)
    }


def _get_match_reason(source: str, genre_match: float, director_match: float, actor_match: float, in_watchlist: bool) -> str:
    """Generate a human-readable reason for why this movie was recommended"""
    reasons = []
    
    if in_watchlist:
        reasons.append("On your watchlist")
    if director_match > 0.5:
        reasons.append("Director you love")
    if genre_match > 0.5:
        reasons.append("Your favorite genre")
    if actor_match > 0.3:
        reasons.append("Cast you enjoy")
    if source == "similar":
        reasons.append("Similar to movies you rated highly")
    if source == "trending" and not reasons:
        reasons.append("Trending now")
    
    if not reasons:
        reasons.append("Recommended for you")
    
    return reasons[0]  # Return primary reason


@api_router.get("/movies/explore-for-you")
async def get_explore_for_you(current_user: dict = Depends(get_current_user)):
    """
    Personalized Explore: Discover new movies based on user's tastes.
    Same logic as Curated For You but EXCLUDES:
    - Movies in user's watchlist (they already know about these)
    - Movies in user's watch history (they've already seen these)
    
    Goal: Help users discover new films they haven't seen or considered.
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # If user not logged in, return trending movies as fallback
    if not current_user:
        data = tmdb_request("/trending/movie/week")
        if not data:
            raise HTTPException(status_code=500, detail="Failed to fetch movies")
        return {"results": data.get("results", [])[:20], "personalized": False}
    
    user_id = current_user["id"]
    
    # 1. Get user's watch history with ratings and watch data
    watch_history = await db.watch_history.find(
        {"user_id": user_id},
        {"_id": 0, "tmdb_id": 1, "user_rating": 1, "watch_count": 1, "watches": 1, "last_watched_date": 1}
    ).to_list(500)
    
    # 2. Get user's watchlist - these will be EXCLUDED
    watchlist = await db.watchlist.find(
        {"user_id": user_id},
        {"_id": 0, "tmdb_id": 1}
    ).to_list(200)
    watchlist_ids = set(w["tmdb_id"] for w in watchlist)
    watched_ids = set(h["tmdb_id"] for h in watch_history)
    
    # Movies to exclude (both watched AND in watchlist)
    excluded_ids = watched_ids | watchlist_ids
    
    # 3. Calculate genre/actor/director preferences from watch history
    genre_scores = {}
    director_scores = {}
    actor_scores = {}
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    for h in watch_history:
        tmdb_id = h["tmdb_id"]
        rating = h.get("user_rating", 5.0)
        watch_count = h.get("watch_count", 1) or 1
        
        # Calculate recency boost
        last_watch = h.get("last_watched_date", "")
        recency_boost = 1.0
        if last_watch:
            try:
                watch_date = datetime.fromisoformat(last_watch.replace("Z", "+00:00")) if "T" in last_watch else datetime.strptime(last_watch, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_ago = (now - watch_date).days
                recency_boost = max(0.5, 1.0 - (days_ago / 365) * 0.5)
            except:
                recency_boost = 0.75
        
        # Combined preference weight
        rating_factor = (rating - 5.0) / 5.0
        rewatch_bonus = 1.0 + 0.2 * (watch_count - 1)
        preference_weight = (1.0 + rating_factor) * rewatch_bonus * recency_boost
        
        # Get movie metadata
        cached = await db.tmdb_cache.find_one({"tmdb_id": tmdb_id}, {"_id": 0})
        if cached:
            for genre in cached.get("genres", []):
                name = genre.get("name") if isinstance(genre, dict) else genre
                if name:
                    genre_scores[name] = genre_scores.get(name, 0) + preference_weight
            
            for director in cached.get("directors", []):
                name = director.get("name") if isinstance(director, dict) else director
                if name:
                    director_scores[name] = director_scores.get(name, 0) + preference_weight
            
            for actor in cached.get("cast", [])[:5]:
                name = actor.get("name") if isinstance(actor, dict) else actor
                if name:
                    actor_scores[name] = actor_scores.get(name, 0) + preference_weight * 0.5
    
    # Normalize scores
    max_genre = max(genre_scores.values()) if genre_scores else 1
    max_director = max(director_scores.values()) if director_scores else 1
    max_actor = max(actor_scores.values()) if actor_scores else 1
    
    genre_prefs = {k: v / max_genre for k, v in genre_scores.items()}
    director_prefs = {k: v / max_director for k, v in director_scores.items()}
    actor_prefs = {k: v / max_actor for k, v in actor_scores.items()}
    
    # 4. Get candidate movies (EXCLUDING watchlist and watched)
    candidate_movies = []
    seen_ids = set()
    
    # Source 1: Similar to highly-rated movies in history
    top_rated = sorted(watch_history, key=lambda x: x.get("user_rating", 0), reverse=True)[:7]
    for h in top_rated:
        similar = tmdb_request(f"/movie/{h['tmdb_id']}/similar")
        if similar:
            for m in similar.get("results", [])[:6]:
                if m["id"] not in seen_ids and m["id"] not in excluded_ids:
                    candidate_movies.append({"source": "similar", "data": m})
                    seen_ids.add(m["id"])
    
    # Source 2: Discover movies in favorite genres
    top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    genre_ids = [str(gid) for gname, _ in top_genres for gid, name in GENRE_MAP.items() if name == gname]
    if genre_ids:
        discover_data = tmdb_request("/discover/movie", {
            "sort_by": "vote_average.desc",
            "vote_count.gte": 200,
            "vote_average.gte": 7.0,
            "with_genres": ",".join(genre_ids[:2])
        })
        if discover_data:
            for m in discover_data.get("results", [])[:20]:
                if m["id"] not in seen_ids and m["id"] not in excluded_ids:
                    candidate_movies.append({"source": "genre_match", "data": m})
                    seen_ids.add(m["id"])
    
    # Source 3: Movies by favorite directors
    top_directors = sorted(director_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for director_name, _ in top_directors:
        # Search for director's other movies
        search_data = tmdb_request("/search/person", {"query": director_name})
        if search_data and search_data.get("results"):
            person = search_data["results"][0]
            person_id = person.get("id")
            if person_id:
                credits = tmdb_request(f"/person/{person_id}/movie_credits")
                if credits:
                    for m in credits.get("crew", []):
                        if m.get("job") == "Director" and m.get("id") not in seen_ids and m.get("id") not in excluded_ids:
                            # Fetch full movie data
                            movie_data = tmdb_request(f"/movie/{m['id']}")
                            if movie_data and movie_data.get("vote_count", 0) > 50:
                                candidate_movies.append({"source": "director", "data": movie_data})
                                seen_ids.add(m["id"])
                                if len([c for c in candidate_movies if c["source"] == "director"]) >= 6:
                                    break
    
    # Source 4: Hidden gems (high rating, lower popularity)
    hidden_gems = tmdb_request("/discover/movie", {
        "sort_by": "vote_average.desc",
        "vote_count.gte": 100,
        "vote_count.lte": 1000,
        "vote_average.gte": 7.5
    })
    if hidden_gems:
        for m in hidden_gems.get("results", [])[:10]:
            if m["id"] not in seen_ids and m["id"] not in excluded_ids:
                candidate_movies.append({"source": "hidden_gem", "data": m})
                seen_ids.add(m["id"])
    
    # 5. Calculate curated score for each candidate (NO watchlist boost since we're excluding them)
    scored_movies = []
    
    for candidate in candidate_movies:
        movie = candidate["data"]
        source = candidate["source"]
        tmdb_id = movie.get("id")
        
        # Base score
        curated_score = 0.0
        
        # Genre match scoring
        movie_genres = movie.get("genres", []) or []
        if not movie_genres and movie.get("genre_ids"):
            movie_genres = [{"name": GENRE_MAP.get(gid, "")} for gid in movie.get("genre_ids", [])]
        
        genre_match = 0.0
        for g in movie_genres:
            gname = g.get("name") if isinstance(g, dict) else GENRE_MAP.get(g, "")
            if gname in genre_prefs:
                genre_match += genre_prefs[gname]
        if movie_genres:
            genre_match /= len(movie_genres)
        curated_score += genre_match * 30.0  # Max 30 points for genre match
        
        # Director match scoring
        credits = movie.get("credits", {})
        directors = [c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"]
        director_match = 0.0
        for d in directors:
            if d in director_prefs:
                director_match = max(director_match, director_prefs[d])
        curated_score += director_match * 25.0  # Max 25 points for director match
        
        # Actor match scoring
        cast = credits.get("cast", [])[:5]
        actor_match = 0.0
        for a in cast:
            aname = a.get("name", "")
            if aname in actor_prefs:
                actor_match += actor_prefs[aname]
        if cast:
            actor_match /= len(cast)
        curated_score += actor_match * 15.0  # Max 15 points for actor match
        
        # Quality bonus (TMDB rating)
        vote_avg = movie.get("vote_average", 0)
        vote_count = movie.get("vote_count", 0)
        if vote_count > 100 and vote_avg >= 6.0:
            quality_bonus = (vote_avg - 6.0) / 4.0 * 15.0  # Max 15 points
            curated_score += quality_bonus
        
        # Source bonus
        if source == "similar":
            curated_score += 10.0  # Bonus for being similar to liked movies
        elif source == "director":
            curated_score += 8.0  # Bonus for favorite director's work
        elif source == "hidden_gem":
            curated_score += 5.0  # Bonus for hidden gems
        
        scored_movies.append({
            "id": tmdb_id,
            "title": movie.get("title", ""),
            "poster_path": movie.get("poster_path"),
            "backdrop_path": movie.get("backdrop_path"),
            "overview": movie.get("overview", ""),
            "release_date": movie.get("release_date", ""),
            "vote_average": vote_avg,
            "vote_count": vote_count,
            "genre_ids": movie.get("genre_ids", []),
            "genres": [g.get("name") if isinstance(g, dict) else GENRE_MAP.get(g, str(g)) for g in movie_genres],
            "curated_score": round(curated_score, 1),
            "in_watchlist": False,  # Always false since we exclude watchlist
            "match_reason": _get_explore_match_reason(source, genre_match, director_match, actor_match)
        })
    
    # Sort by curated score (highest first)
    scored_movies.sort(key=lambda x: x["curated_score"], reverse=True)
    
    # Return top 20
    return {
        "results": scored_movies[:20],
        "personalized": True,
        "total_candidates": len(candidate_movies)
    }


def _get_explore_match_reason(source: str, genre_match: float, director_match: float, actor_match: float) -> str:
    """Generate a human-readable reason for why this movie was recommended in Explore"""
    if source == "director" and director_match > 0.3:
        return "From a director you love"
    if source == "similar":
        return "Similar to your favorites"
    if director_match > 0.5:
        return "Director you enjoy"
    if genre_match > 0.5:
        return "Matches your taste"
    if actor_match > 0.3:
        return "Stars you like"
    if source == "hidden_gem":
        return "Hidden gem to discover"
    return "New discovery for you"


# Movie endpoints
@api_router.post("/movies/discover")
async def discover_movies(vibe_params: VibeParams):
    """Discover movies based on vibe parameters"""
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # Map brain power (complexity) to vote_average
    min_rating = 5.0 + (vibe_params.brain_power / 100) * 3  # 5-8 range
    
    # Map mood to genres
    genre_filter = []
    if vibe_params.mood < 33:  # Need a cry - Drama, Thriller
        genre_filter = [18, 53, 10749]  # Drama, Thriller, Romance
    elif vibe_params.mood > 67:  # Pure joy - Comedy, Animation
        genre_filter = [35, 16, 10751, 12]  # Comedy, Animation, Family, Adventure
    
    # Map energy to action-oriented or slow-paced genres
    if vibe_params.energy > 67:
        genre_filter.extend([28, 12, 878])  # Action, Adventure, Sci-Fi
    elif vibe_params.energy < 33:
        genre_filter = [g for g in genre_filter if g not in [28, 12]]  # Remove action
    
    # Build TMDB discover params
    discover_params = {
        "sort_by": "vote_average.desc",
        "vote_count.gte": 100,
        "vote_average.gte": min_rating,
        "page": vibe_params.page
    }
    
    if genre_filter:
        discover_params["with_genres"] = ",".join(str(g) for g in genre_filter[:3])
    
    data = tmdb_request("/discover/movie", discover_params)
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch movies from TMDB")
    
    # Get user for scoring
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    user_birth_year = user.get("birth_year", 1995) if user else 1995
    user_id = user.get("id", "") if user else ""
    
    # Score and enhance movies
    scored_movies = []
    for movie in data.get("results", []):
        scored = await calculate_flick_score(movie, user_id, user_birth_year, vibe_params)
        scored_movies.append(scored)
    
    # Sort by match percentage
    scored_movies.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    return {
        "results": scored_movies,
        "page": data.get("page", 1),
        "total_pages": data.get("total_pages", 1),
        "total_results": data.get("total_results", 0)
    }

@api_router.get("/movies/trending")
async def get_trending_movies():
    """Get trending movies for hero section"""
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    data = tmdb_request("/trending/movie/week")
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch trending movies")
    
    movies = []
    for movie in data.get("results", [])[:10]:
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        movies.append({
            **movie,
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
        })
    
    return {"results": movies}

# ============ SECTION ENDPOINTS ============

@api_router.get("/movies/sections/chefs-special")
async def get_chefs_special():
    """
    Chef's Special: Recent movies that critics like the most
    - High vote average
    - Recent releases (last 2 years)
    - Good vote count (critical mass)
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # Get critically acclaimed recent movies
    current_year = datetime.now().year
    data = tmdb_request("/discover/movie", {
        "sort_by": "vote_average.desc",
        "vote_count.gte": 500,
        "vote_average.gte": 7.5,
        "primary_release_date.gte": f"{current_year - 2}-01-01",
        "page": 1
    })
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch chef's special")
    
    movies = []
    for movie in data.get("results", [])[:12]:
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        movies.append({
            **movie,
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
            "vibe_tag": "Critics' favorite",
            "match_percentage": min(int(movie.get("vote_average", 0) * 10), 100)
        })
    
    return {"results": movies}

@api_router.get("/movies/sections/certified-swangy")
async def get_certified_swangy():
    """
    Certified Swangy: Most trending movies in the last two weeks
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # Get trending movies (daily for more recent)
    data = tmdb_request("/trending/movie/day")
    
    if not data:
        # Fallback to weekly
        data = tmdb_request("/trending/movie/week")
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch trending")
    
    movies = []
    for movie in data.get("results", [])[:12]:
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        
        # Calculate "swangy" score based on popularity
        popularity = movie.get("popularity", 0)
        swangy_score = min(int(70 + (popularity / 100) * 30), 100)
        
        movies.append({
            **movie,
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
            "vibe_tag": "Trending now",
            "match_percentage": swangy_score
        })
    
    return {"results": movies}

@api_router.get("/movies/sections/all-time-classics")
async def get_all_time_classics():
    """
    All Time Classics: Highly rated, highly watched classic movies
    - High vote average
    - Very high vote count (stood test of time)
    - Released before 2010
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # Get classic highly-rated movies
    data = tmdb_request("/discover/movie", {
        "sort_by": "vote_average.desc",
        "vote_count.gte": 5000,
        "vote_average.gte": 8.0,
        "primary_release_date.lte": "2010-12-31",
        "page": 1
    })
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch classics")
    
    movies = []
    for movie in data.get("results", [])[:12]:
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        
        # Classics get high match percentage
        movies.append({
            **movie,
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
            "vibe_tag": "Timeless classic",
            "match_percentage": min(int(movie.get("vote_average", 0) * 10) + 5, 100)
        })
    
    return {"results": movies}

@api_router.get("/movies/sections/explore")
async def get_explore_movies():
    """
    Explore: Movies NOT similar to user's usual tastes
    - Different genres from what user typically watches
    - Highly rated and popular
    - Not in user's watch history
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    
    # Get user's watched genres and movie IDs
    user_genres = set()
    watched_ids = set()
    
    if user:
        watch_history = await db.watch_history.find(
            {"user_id": user["id"]},
            {"_id": 0}
        ).to_list(100)
        
        for movie in watch_history:
            watched_ids.add(movie.get("tmdb_id"))
            # Fetch genre info
            details = tmdb_request(f"/movie/{movie['tmdb_id']}")
            if details:
                for genre in details.get("genres", []):
                    user_genres.add(genre.get("id"))
    
    # All available genres
    all_genre_ids = set(GENRE_MAP.keys())
    
    # Find genres user hasn't explored much
    unexplored_genres = all_genre_ids - user_genres
    
    # Build discover params
    discover_params = {
        "sort_by": "popularity.desc",
        "vote_count.gte": 500,
        "vote_average.gte": 7.0,
        "page": 1
    }
    
    # If there are unexplored genres, prioritize them
    if unexplored_genres:
        explore_genre_list = list(unexplored_genres)[:3]
        discover_params["with_genres"] = "|".join(str(g) for g in explore_genre_list)  # OR condition
    
    # Fetch movies
    data = tmdb_request("/discover/movie", discover_params)
    
    if not data or not data.get("results"):
        # Fallback to popular movies
        data = tmdb_request("/movie/popular")
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch explore movies")
    
    movies = []
    for movie in data.get("results", []):
        # Skip watched movies
        if movie.get("id") in watched_ids:
            continue
        if len(movies) >= 12:
            break
            
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        
        movies.append({
            **movie,
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
            "vibe_tag": "Expand your horizons",
            "match_percentage": min(int(movie.get("vote_average", 0) * 10), 100)
        })
    
    return {"results": movies}

# Popular movie collections/franchises for Marathon section
POPULAR_COLLECTIONS = [
    {"id": 10, "name": "Star Wars Collection"},
    {"id": 119, "name": "The Lord of the Rings Collection"},
    {"id": 1241, "name": "Harry Potter Collection"},
    {"id": 131296, "name": "Spider-Man (MCU) Collection"},
    {"id": 86311, "name": "The Avengers Collection"},
    {"id": 528, "name": "The Godfather Collection"},
    {"id": 2326, "name": "The Matrix Collection"},
    {"id": 9485, "name": "The Fast and the Furious Collection"},
    {"id": 656, "name": "Saw Collection"},
    {"id": 748, "name": "X-Men Collection"},
    {"id": 87096, "name": "Avatar Collection"},
    {"id": 295, "name": "Pirates of the Caribbean Collection"},
    {"id": 263, "name": "The Dark Knight Collection"},
    {"id": 121938, "name": "The Hobbit Collection"},
    {"id": 84, "name": "Indiana Jones Collection"},
    {"id": 8091, "name": "Alien Collection"},
    {"id": 1570, "name": "Die Hard Collection"},
    {"id": 328, "name": "Jurassic Park Collection"},
    {"id": 2806, "name": "American Pie Collection"},
    {"id": 230, "name": "The Terminator Collection"},
]

@api_router.get("/movies/sections/marathon")
async def get_marathon_collections():
    """
    Marathon: Movie collections/franchises
    Each card represents an entire movie universe (trilogy, saga, etc.)
    """
    collections = []
    
    for coll in POPULAR_COLLECTIONS[:12]:
        coll_data = tmdb_request(f"/collection/{coll['id']}")
        
        if coll_data:
            parts = coll_data.get("parts", [])
            movie_count = len(parts)
            
            # Calculate total runtime and average rating
            total_runtime = 0
            total_rating = 0
            rating_count = 0
            
            for part in parts:
                if part.get("vote_average"):
                    total_rating += part.get("vote_average", 0)
                    rating_count += 1
            
            avg_rating = total_rating / rating_count if rating_count > 0 else 0
            
            # Get years span
            years = [p.get("release_date", "")[:4] for p in parts if p.get("release_date")]
            years = [y for y in years if y]
            year_span = f"{min(years)} - {max(years)}" if len(years) >= 2 else (years[0] if years else "")
            
            collections.append({
                "id": coll_data.get("id"),
                "name": coll_data.get("name"),
                "overview": coll_data.get("overview", ""),
                "poster_url": get_image_url(coll_data.get("poster_path"), "w500"),
                "backdrop_url": get_image_url(coll_data.get("backdrop_path"), "w1280"),
                "movie_count": movie_count,
                "year_span": year_span,
                "avg_rating": round(avg_rating, 1),
                "vibe_tag": f"{movie_count} films to binge",
                "match_percentage": min(int(avg_rating * 10) + 5, 100),
                "parts": [
                    {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "release_date": p.get("release_date"),
                        "poster_url": get_image_url(p.get("poster_path"), "w342")
                    }
                    for p in sorted(parts, key=lambda x: x.get("release_date", "") or "9999")
                ],
                "is_collection": True
            })
    
    return {"results": collections}

@api_router.get("/movies/emergency")
async def get_emergency_recommendations():
    """
    'I Can't Even' button - Get top 3 rewatches
    Returns films where user_rating >= 8 AND last_watched_date > 365 days ago
    """
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    
    # Find high-rated, not recently watched movies
    comfort_movies = await db.watch_history.find(
        {
            "user_id": user["id"],
            "user_rating": {"$gte": 8},
            "last_watched_date": {"$lt": one_year_ago}
        },
        {"_id": 0}
    ).sort("user_rating", -1).limit(3).to_list(3)
    
    # If not enough results, relax the date constraint
    if len(comfort_movies) < 3:
        all_high_rated = await db.watch_history.find(
            {
                "user_id": user["id"],
                "user_rating": {"$gte": 8}
            },
            {"_id": 0}
        ).sort("user_rating", -1).limit(3).to_list(3)
        comfort_movies = all_high_rated
    
    # Enrich with TMDB data
    enriched = []
    for movie in comfort_movies:
        tmdb_id = movie.get("tmdb_id")
        details = tmdb_request(f"/movie/{tmdb_id}")
        if details:
            enriched.append({
                **movie,
                "title": details.get("title", movie.get("title", "Unknown")),
                "poster_url": get_image_url(details.get("poster_path"), "w500"),
                "backdrop_url": get_image_url(details.get("backdrop_path"), "w1280"),
                "overview": details.get("overview", ""),
                "vibe_tag": "Your comfort classic"
            })
        else:
            enriched.append({
                **movie,
                "poster_url": get_image_url(movie.get("poster_path"), "w500") if movie.get("poster_path") else None,
                "vibe_tag": "Your comfort classic"
            })
    
    return {"results": enriched}

@api_router.get("/movies/random-picks")
async def get_random_movie_picks():
    """
    Random Movie Picks:
    - If user has rated movies: Return 3 movies similar to user's top 20 highest rated
    - If no rated movies: Return 3 random popular movies from TMDB
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    
    recommendations = []
    
    if user:
        # Get user's top 20 highest rated movies
        top_rated = await db.watch_history.find(
            {"user_id": user["id"]},
            {"_id": 0}
        ).sort("user_rating", -1).limit(20).to_list(20)
        
        if top_rated and len(top_rated) >= 1:
            # Collect genres from top rated movies to find similar
            genre_counts = {}
            for movie in top_rated:
                details = tmdb_request(f"/movie/{movie['tmdb_id']}")
                if details:
                    for genre in details.get("genres", []):
                        gid = genre.get("id")
                        if gid:
                            genre_counts[gid] = genre_counts.get(gid, 0) + movie.get("user_rating", 5)
            
            # Get top genres by weighted count
            top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            top_genre_ids = [g[0] for g in top_genres]
            
            # Get similar movies based on favorite genres
            if top_genre_ids:
                similar_data = tmdb_request("/discover/movie", {
                    "sort_by": "vote_average.desc",
                    "vote_count.gte": 200,
                    "with_genres": ",".join(str(g) for g in top_genre_ids),
                    "page": 1
                })
                
                if similar_data and similar_data.get("results"):
                    # Filter out movies already in watch history
                    watched_ids = {m["tmdb_id"] for m in top_rated}
                    candidates = [m for m in similar_data["results"] if m["id"] not in watched_ids]
                    
                    # Randomly pick 3 from top 10 candidates
                    import random
                    top_candidates = candidates[:10]
                    random.shuffle(top_candidates)
                    selected = top_candidates[:3]
                    
                    for movie in selected:
                        genre_ids = movie.get("genre_ids", [])
                        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
                        recommendations.append({
                            **movie,
                            "genres": genres,
                            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
                            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
                            "vibe_tag": "Based on your favorites",
                            "match_percentage": min(85 + int(movie.get("vote_average", 0)), 99)
                        })
    
    # Fallback: Get popular movies if no recommendations yet
    if len(recommendations) < 3:
        popular_data = tmdb_request("/movie/popular", {"page": 1})
        
        if popular_data and popular_data.get("results"):
            import random
            candidates = popular_data["results"][:20]
            random.shuffle(candidates)
            
            # Fill remaining slots
            for movie in candidates:
                if len(recommendations) >= 3:
                    break
                # Skip if already in recommendations
                if any(r.get("id") == movie.get("id") for r in recommendations):
                    continue
                    
                genre_ids = movie.get("genre_ids", [])
                genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
                recommendations.append({
                    **movie,
                    "genres": genres,
                    "poster_url": get_image_url(movie.get("poster_path"), "w500"),
                    "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
                    "vibe_tag": "Popular pick",
                    "match_percentage": min(70 + int(movie.get("vote_average", 0) * 2), 95)
                })
    
    return {"results": recommendations[:3]}

class ComfortRequest(BaseModel):
    hour: int = 12  # Hour of day (0-23)
    is_cold: bool = False  # Weather condition
    is_rainy: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Weather cache (short TTL since weather changes)
weather_cache = {}
WEATHER_CACHE_TTL = 1800  # 30 minutes

def fetch_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather from Open-Meteo API (free, no key needed)"""
    cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
    cached = weather_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < WEATHER_CACHE_TTL:
        return cached["data"]
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "hourly": "temperature_2m,relative_humidity_2m,rain,weathercode",
            "forecast_days": 1,
            "timezone": "auto"
        }
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        current = data.get("current_weather", {})
        temperature = current.get("temperature", 20)
        weathercode = current.get("weathercode", 0)
        
        # WMO Weather codes: 0-3 clear/cloudy, 45-48 fog, 51-67 drizzle/rain, 71-77 snow, 80-99 showers/thunderstorms
        is_rainy = weathercode in range(51, 100) or weathercode in [45, 48]
        is_cold = temperature < 12
        is_snowy = weathercode in range(71, 78)
        is_hot = temperature > 30
        
        weather_data = {
            "temperature": temperature,
            "weathercode": weathercode,
            "is_cold": is_cold,
            "is_rainy": is_rainy,
            "is_snowy": is_snowy,
            "is_hot": is_hot,
            "description": get_weather_description(weathercode, temperature)
        }
        
        weather_cache[cache_key] = {"data": weather_data, "ts": time.time()}
        return weather_data
    except Exception as e:
        logging.error(f"Weather API failed: {e}")
        return {"temperature": 20, "weathercode": 0, "is_cold": False, "is_rainy": False, "is_snowy": False, "is_hot": False, "description": ""}

def get_weather_description(weathercode: int, temperature: float) -> str:
    """Convert WMO weather code to human description"""
    if weathercode <= 3:
        base = "clear skies" if weathercode <= 1 else "partly cloudy"
    elif weathercode <= 48:
        base = "foggy"
    elif weathercode <= 57:
        base = "light drizzle"
    elif weathercode <= 67:
        base = "rainy"
    elif weathercode <= 77:
        base = "snowy"
    elif weathercode <= 82:
        base = "rain showers"
    else:
        base = "stormy"
    
    if temperature < 0:
        return f"Freezing & {base}"
    elif temperature < 12:
        return f"Chilly & {base}"
    elif temperature > 30:
        return f"Hot & {base}"
    return base.capitalize()

# Cache for comfort recommendations (stable unless history changes)
comfort_cache = {}

def generate_comfort_vibe_tag(watch_count: int, user_rating: int, hour: int, is_cold: bool, is_rainy: bool, is_snowy: bool, weather_description: str) -> str:
    """Generate context-aware vibe tag for comfort movies"""
    if watch_count >= 3:
        return "Your go-to comfort classic"
    if is_snowy:
        return "Perfect for a snowy day indoors"
    if is_rainy:
        return "Ideal for a rainy day"
    if is_cold:
        return "Warm up with this favorite"
    if user_rating >= 9:
        return "A certified favorite"
    if hour >= 22 or hour < 6:
        return "Perfect for late night unwinding"
    if hour >= 18:
        return "Evening comfort pick"
    return "Comfort food for your soul"

@api_router.post("/movies/comfort")
async def get_comfort_movies(request: ComfortRequest):
    """
    Comfort Movies - Context-aware recommendations based on:
    1. User's most re-watched and highest rated movies
    2. Time of day (later = user more tired, prefer lighter content)
    3. Real weather/climate from user's location (Open-Meteo API)
    
    Returns same 3 movies unless watch history or context changes.
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_id = user["id"]
    
    # Fetch real weather if location provided
    weather = None
    is_cold = request.is_cold
    is_rainy = request.is_rainy
    is_snowy = False
    weather_description = ""
    temperature = None
    
    if request.latitude is not None and request.longitude is not None:
        weather = fetch_weather(request.latitude, request.longitude)
        is_cold = weather.get("is_cold", False)
        is_rainy = weather.get("is_rainy", False)
        is_snowy = weather.get("is_snowy", False)
        temperature = weather.get("temperature")
        weather_description = weather.get("description", "")
    
    # Get watch history hash to detect changes
    watch_history = await db.watch_history.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Create a hash of watch history + context to detect changes
    context_key = f"{is_cold}_{is_rainy}_{is_snowy}_{request.hour // 6}"
    history_hash = hash(frozenset(
        (m.get("tmdb_id"), m.get("user_rating"), m.get("watch_count")) 
        for m in watch_history
    ))
    
    # Check cache (include weather context in key)
    cache_key = f"{user_id}_{context_key}"
    cached = comfort_cache.get(cache_key)
    if cached and cached.get("history_hash") == history_hash:
        return {"results": cached["movies"], "cached": True, "weather": weather_description}
    
    # Calculate comfort scores for each watched movie
    comfort_movies = []
    
    for movie in watch_history:
        rating = movie.get("user_rating", 5)
        watch_count = movie.get("watch_count", 1)
        
        # Base comfort score: combination of rating and rewatch count
        comfort_score = (rating * 1.5) + (watch_count * 3)
        
        # Time of day adjustment
        # Late night (22-6): prefer lighter, familiar content
        # Evening (18-22): good for any comfort movie
        # Day (6-18): slightly lower comfort need
        if request.hour >= 22 or request.hour < 6:
            comfort_score *= 1.3  # Late night boost
        elif request.hour >= 18:
            comfort_score *= 1.1  # Evening boost
        
        # Weather-based adjustments
        if is_cold or is_rainy or is_snowy:
            comfort_score *= 1.25  # Cozy weather boost - perfect comfort movie weather
        
        if is_snowy:
            comfort_score *= 1.1  # Extra snowy day bonus
        
        # Only consider movies rated 7+ as true comfort movies
        if rating >= 7:
            comfort_movies.append({
                **movie,
                "comfort_score": comfort_score
            })
    
    # Sort by comfort score
    comfort_movies.sort(key=lambda x: x["comfort_score"], reverse=True)
    
    # Take top 3
    top_comfort = comfort_movies[:3]
    
    # Enrich with TMDB data
    enriched = []
    for movie in top_comfort:
        tmdb_id = movie.get("tmdb_id")
        details = tmdb_request(f"/movie/{tmdb_id}")
        
        # Generate context-aware vibe tag
        watch_count = movie.get("watch_count", 1)
        vibe_tag = generate_comfort_vibe_tag(
            watch_count=watch_count,
            user_rating=movie.get("user_rating", 0),
            hour=request.hour,
            is_cold=is_cold,
            is_rainy=is_rainy,
            is_snowy=is_snowy,
            weather_description=weather_description
        )
        
        if details:
            enriched.append({
                "id": tmdb_id,
                "tmdb_id": tmdb_id,
                "title": details.get("title", movie.get("title", "Unknown")),
                "poster_url": get_image_url(details.get("poster_path"), "w500"),
                "backdrop_url": get_image_url(details.get("backdrop_path"), "w1280"),
                "overview": details.get("overview", ""),
                "user_rating": movie.get("user_rating"),
                "watch_count": watch_count,
                "vibe_tag": vibe_tag,
                "comfort_score": round(movie.get("comfort_score", 0), 1)
            })
        else:
            enriched.append({
                **movie,
                "poster_url": get_image_url(movie.get("poster_path"), "w500") if movie.get("poster_path") else None,
                "vibe_tag": vibe_tag
            })
    
    # If not enough comfort movies, add highest rated from history
    if len(enriched) < 3:
        remaining_needed = 3 - len(enriched)
        existing_ids = {m.get("tmdb_id") for m in enriched}
        
        # Get remaining high-rated movies
        for movie in watch_history:
            if movie.get("tmdb_id") not in existing_ids and movie.get("user_rating", 0) >= 6:
                tmdb_id = movie.get("tmdb_id")
                details = tmdb_request(f"/movie/{tmdb_id}")
                if details:
                    enriched.append({
                        "id": tmdb_id,
                        "tmdb_id": tmdb_id,
                        "title": details.get("title", movie.get("title", "Unknown")),
                        "poster_url": get_image_url(details.get("poster_path"), "w500"),
                        "backdrop_url": get_image_url(details.get("backdrop_path"), "w1280"),
                        "user_rating": movie.get("user_rating"),
                        "watch_count": movie.get("watch_count", 1),
                        "vibe_tag": "From your collection",
                        "comfort_score": 0
                    })
                    if len(enriched) >= 3:
                        break
    
    # Cache the results
    comfort_cache[cache_key] = {
        "movies": enriched[:3],
        "history_hash": history_hash
    }
    
    return {"results": enriched[:3], "cached": False, "weather": weather_description}

@api_router.get("/movies/{movie_id}")
async def get_movie_details(movie_id: int):
    """Get detailed movie information"""
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    data = tmdb_request(
        f"/movie/{movie_id}",
        {"append_to_response": "credits,videos,similar,recommendations"}
    )
    
    if not data:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Get trailer
    videos = data.get("videos", {}).get("results", [])
    trailer = None
    for v in videos:
        if v.get("type") == "Trailer" and v.get("site") == "YouTube":
            trailer = f"https://www.youtube.com/embed/{v['key']}"
            break
    
    # Get genres as strings
    genres = [g.get("name", "") for g in data.get("genres", [])]
    
    # Check if in user's watch history
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    in_history = False
    user_rating = None
    if user:
        history_entry = await db.watch_history.find_one(
            {"user_id": user["id"], "tmdb_id": movie_id},
            {"_id": 0}
        )
        if history_entry:
            in_history = True
            user_rating = history_entry.get("user_rating")
    
    # Enrich with local IMDB data
    title = data.get("title", "")
    year = int(data.get("release_date", "0000")[:4]) if data.get("release_date") else None
    local_movie = None
    if title and year:
        local_movie = await db.movies.find_one(
            {"title_lower": title.lower(), "year": year},
            {"_id": 0}
        )
    
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date"),
        "runtime": data.get("runtime"),
        "vote_average": data.get("vote_average"),
        "vote_count": data.get("vote_count"),
        "genres": genres,
        "poster_url": get_image_url(data.get("poster_path"), "w500"),
        "backdrop_url": get_image_url(data.get("backdrop_path"), "w1280"),
        "trailer_url": trailer,
        "in_history": in_history,
        "user_rating": user_rating,
        "cast": [
            {
                "name": c.get("name"),
                "character": c.get("character"),
                "profile_url": get_image_url(c.get("profile_path"), "w185")
            }
            for c in data.get("credits", {}).get("cast", [])[:10]
        ],
        "similar": [
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "poster_url": get_image_url(m.get("poster_path"), "w342")
            }
            for m in data.get("similar", {}).get("results", [])[:6]
        ],
        # Local IMDB enrichment
        "imdb_rating": local_movie.get("imdb_rating") if local_movie else None,
        "imdb_votes": local_movie.get("imdb_votes") if local_movie else None,
        "meta_score": local_movie.get("meta_score") if local_movie else None,
        "budget": local_movie.get("budget") if local_movie else None,
        "gross_worldwide": local_movie.get("gross_worldwide") if local_movie else None,
        "gross_us_canada": local_movie.get("gross_us_canada") if local_movie else None,
        "awards": local_movie.get("awards") if local_movie else None,
        "mpa": local_movie.get("mpa") if local_movie else None,
        "imdb_description": local_movie.get("description") if local_movie else None,
    }

# ============ STREAMING AVAILABILITY ============

SERVICE_DISPLAY = {
    "netflix": {"name": "Netflix", "color": "#E50914"},
    "prime": {"name": "Prime Video", "color": "#00A8E1"},
    "disney": {"name": "Disney+", "color": "#113CCF"},
    "hulu": {"name": "Hulu", "color": "#1CE783"},
    "apple": {"name": "Apple TV+", "color": "#A2AAAD"},
    "hbo": {"name": "Max", "color": "#002BE7"},
    "paramount": {"name": "Paramount+", "color": "#0064FF"},
}

def fetch_streaming_availability(tmdb_id: int, country: str = "us") -> list:
    """Fetch streaming availability from Movies of the Night API with MongoDB caching"""
    try:
        url = f"{STREAMING_API_BASE}/shows/movie/{tmdb_id}"
        headers = {
            "x-rapidapi-host": "streaming-availability.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {"country": country}
        
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 404:
            return []
        res.raise_for_status()
        data = res.json()
        
        streaming_options = data.get("streamingOptions", {})
        country_options = streaming_options.get(country, [])
        
        # Filter to allowed services and build clean response
        results = []
        seen_services = set()
        for opt in country_options:
            svc = opt.get("service", {})
            svc_id = svc.get("id", "")
            
            if svc_id not in ALLOWED_SERVICES:
                continue
            
            # For subscription type, only keep one entry per service
            opt_type = opt.get("type", "")
            dedup_key = f"{svc_id}_{opt_type}"
            if dedup_key in seen_services:
                continue
            seen_services.add(dedup_key)
            
            display = SERVICE_DISPLAY.get(svc_id, {})
            entry = {
                "service_id": svc_id,
                "service_name": display.get("name", svc.get("name", svc_id)),
                "service_color": display.get("color", "#ffffff"),
                "type": opt_type,
                "link": opt.get("link", ""),
                "quality": opt.get("quality", ""),
            }
            
            price = opt.get("price")
            if price:
                entry["price"] = price.get("formatted", "")
                entry["price_amount"] = price.get("amount", 0)
                entry["price_currency"] = price.get("currency", "")
            
            results.append(entry)
        
        # Sort: subscription first, then free, then rent, then buy
        type_order = {"subscription": 0, "free": 1, "addon": 2, "rent": 3, "buy": 4}
        results.sort(key=lambda x: type_order.get(x["type"], 5))
        
        return results
    except Exception as e:
        logging.error(f"Streaming API failed for movie {tmdb_id}: {e}")
        return []

@api_router.get("/movies/{movie_id}/streaming")
async def get_streaming_availability(movie_id: int, country: str = "us"):
    """Get streaming availability for a movie, with 24h MongoDB cache"""
    if not RAPIDAPI_KEY:
        raise HTTPException(status_code=500, detail="Streaming API not configured")
    
    country = country.lower()[:2]
    
    # Check MongoDB cache
    cached = await db.streaming_cache.find_one(
        {"tmdb_id": movie_id, "country": country},
        {"_id": 0}
    )
    
    if cached:
        # Check if cache is still fresh (24 hours)
        cached_at = cached.get("cached_at", "")
        if cached_at:
            try:
                cache_time = datetime.fromisoformat(cached_at)
                if (datetime.now(timezone.utc) - cache_time).total_seconds() < 86400:
                    return {"results": cached.get("options", []), "country": country, "cached": True}
            except (ValueError, TypeError):
                pass
    
    # Fetch from API
    options = fetch_streaming_availability(movie_id, country)
    
    # Store in MongoDB cache
    await db.streaming_cache.update_one(
        {"tmdb_id": movie_id, "country": country},
        {"$set": {
            "tmdb_id": movie_id,
            "country": country,
            "options": options,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"results": options, "country": country, "cached": False}

# ============ FEELING SEARCH (Chat Feature) ============

# Feeling to genre/keyword mapping for semantic search
FEELING_MAPPINGS = {
    # Emotions
    "happy": {"genres": [35, 16, 10751], "keywords": ["feel-good", "comedy", "joy", "happy"]},
    "sad": {"genres": [18, 10749], "keywords": ["emotional", "tragic", "tearjerker", "drama"]},
    "excited": {"genres": [28, 12, 878], "keywords": ["action", "adventure", "thrilling"]},
    "scared": {"genres": [27, 53], "keywords": ["horror", "scary", "thriller", "suspense"]},
    "romantic": {"genres": [10749], "keywords": ["love", "romance", "romantic"]},
    "nostalgic": {"genres": [16, 10751, 14], "keywords": ["classic", "childhood", "nostalgia"]},
    "relaxed": {"genres": [35, 16, 10751], "keywords": ["calm", "peaceful", "light"]},
    "anxious": {"genres": [53, 9648], "keywords": ["mystery", "suspense", "psychological"]},
    "inspired": {"genres": [18, 36], "keywords": ["inspiring", "motivational", "true story"]},
    "lonely": {"genres": [18, 10749], "keywords": ["solitude", "isolation", "connection"]},
    "angry": {"genres": [28, 80], "keywords": ["revenge", "action", "crime"]},
    "curious": {"genres": [99, 878, 9648], "keywords": ["documentary", "science", "mystery"]},
    "bored": {"genres": [28, 12, 35], "keywords": ["entertaining", "fun", "exciting"]},
    "tired": {"genres": [35, 16], "keywords": ["light", "easy", "comfort"]},
    "adventurous": {"genres": [12, 14, 878], "keywords": ["adventure", "journey", "epic"]},
    
    # Moods/Vibes
    "chill": {"genres": [35, 16, 10402], "keywords": ["relaxing", "calm", "easy"]},
    "intense": {"genres": [28, 53, 80], "keywords": ["intense", "gripping", "edge"]},
    "funny": {"genres": [35], "keywords": ["comedy", "hilarious", "laugh"]},
    "dark": {"genres": [27, 53, 80], "keywords": ["dark", "noir", "gritty"]},
    "uplifting": {"genres": [35, 18, 10751], "keywords": ["uplifting", "heartwarming", "hope"]},
    "mind-bending": {"genres": [878, 9648, 53], "keywords": ["twist", "complex", "psychological"]},
    "epic": {"genres": [12, 14, 28], "keywords": ["epic", "grand", "spectacular"]},
    "cozy": {"genres": [35, 10751, 16], "keywords": ["comfort", "warm", "feel-good"]},
    
    # Situations
    "rainy": {"genres": [18, 10749], "keywords": ["rainy day", "cozy", "melancholic"]},
    "date": {"genres": [10749, 35], "keywords": ["romantic", "date night", "love"]},
    "family": {"genres": [10751, 16, 12], "keywords": ["family", "kids", "animated"]},
    "friends": {"genres": [35, 28, 12], "keywords": ["fun", "group", "entertaining"]},
    "alone": {"genres": [18, 53, 9648], "keywords": ["solo", "introspective", "deep"]},
    "party": {"genres": [35, 10402], "keywords": ["fun", "dance", "music"]},
    "weekend": {"genres": [28, 12, 35], "keywords": ["blockbuster", "entertaining"]},
    "late night": {"genres": [27, 53, 9648], "keywords": ["thriller", "mystery", "suspense"]},
    
    # Direct genre mentions
    "action": {"genres": [28], "keywords": ["action", "fighting", "explosive"]},
    "comedy": {"genres": [35], "keywords": ["comedy", "funny", "laugh"]},
    "horror": {"genres": [27], "keywords": ["horror", "scary", "fear"]},
    "drama": {"genres": [18], "keywords": ["drama", "emotional", "serious"]},
    "sci-fi": {"genres": [878], "keywords": ["science fiction", "future", "space"]},
    "fantasy": {"genres": [14], "keywords": ["fantasy", "magic", "mythical"]},
    "thriller": {"genres": [53], "keywords": ["thriller", "suspense", "tense"]},
    "animation": {"genres": [16], "keywords": ["animated", "cartoon", "pixar"]},
    "documentary": {"genres": [99], "keywords": ["documentary", "real", "true"]},
    "romance": {"genres": [10749], "keywords": ["romance", "love", "relationship"]},
}

class FeelingSearchRequest(BaseModel):
    query: str
    page: int = 1

def parse_feeling_query(query: str) -> dict:
    """Parse user's feeling query and extract relevant genres and keywords"""
    query_lower = query.lower()
    matched_genres = set()
    matched_keywords = []
    
    # Check for feeling matches
    for feeling, mapping in FEELING_MAPPINGS.items():
        if feeling in query_lower:
            matched_genres.update(mapping["genres"])
            matched_keywords.extend(mapping["keywords"])
    
    # If no direct matches, try to infer from common words
    if not matched_genres:
        # Default mood detection
        positive_words = ["good", "great", "amazing", "love", "enjoy", "fun", "laugh", "smile"]
        negative_words = ["cry", "sad", "down", "depressed", "melancholy", "blue"]
        intense_words = ["edge", "thrill", "intense", "gripping", "suspense", "heart"]
        relaxed_words = ["relax", "calm", "peaceful", "quiet", "easy", "light", "chill"]
        
        for word in positive_words:
            if word in query_lower:
                matched_genres.update([35, 16, 10751])  # Comedy, Animation, Family
                break
        
        for word in negative_words:
            if word in query_lower:
                matched_genres.update([18, 10749])  # Drama, Romance
                break
        
        for word in intense_words:
            if word in query_lower:
                matched_genres.update([28, 53, 27])  # Action, Thriller, Horror
                break
        
        for word in relaxed_words:
            if word in query_lower:
                matched_genres.update([35, 16, 10402])  # Comedy, Animation, Music
                break
    
    # Default fallback - trending/popular
    if not matched_genres:
        matched_genres = {28, 35, 18, 12}  # Action, Comedy, Drama, Adventure
    
    return {
        "genres": list(matched_genres)[:3],
        "keywords": matched_keywords[:5],
        "original_query": query
    }

def generate_feeling_vibe_tag(query: str, movie: dict) -> str:
    """Generate a vibe tag based on the user's feeling query"""
    query_lower = query.lower()
    
    # Match specific feelings to tags
    if any(w in query_lower for w in ["happy", "joy", "fun", "laugh"]):
        return "Perfect for lifting your spirits"
    if any(w in query_lower for w in ["sad", "cry", "emotional"]):
        return "Get ready for the feels"
    if any(w in query_lower for w in ["scared", "horror", "spooky"]):
        return "Will keep you on edge"
    if any(w in query_lower for w in ["romantic", "love", "date"]):
        return "Romantic vibes guaranteed"
    if any(w in query_lower for w in ["excited", "action", "thrill"]):
        return "Non-stop adrenaline"
    if any(w in query_lower for w in ["tired", "relax", "chill", "cozy"]):
        return "Easy comfort viewing"
    if any(w in query_lower for w in ["nostalgic", "classic", "childhood"]):
        return "A blast from the past"
    if any(w in query_lower for w in ["curious", "mind", "think"]):
        return "Food for thought"
    if any(w in query_lower for w in ["alone", "lonely", "solo"]):
        return "Perfect solo watch"
    if any(w in query_lower for w in ["friends", "group", "party"]):
        return "Great with friends"
    
    return f"Matches your '{query[:20]}...' vibe"

@api_router.post("/movies/feeling-search")
async def feeling_search(request: FeelingSearchRequest):
    """
    Search movies based on how the user is feeling.
    Takes natural language input and returns relevant movies.
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    # Parse the feeling query
    parsed = parse_feeling_query(request.query)
    
    # Search TMDB with parsed genres
    discover_params = {
        "sort_by": "popularity.desc",
        "vote_count.gte": 50,
        "page": request.page
    }
    
    if parsed["genres"]:
        discover_params["with_genres"] = ",".join(str(g) for g in parsed["genres"])
    
    data = tmdb_request("/discover/movie", discover_params)
    
    if not data:
        # Fallback to trending if discover fails
        data = tmdb_request("/trending/movie/week")
    
    if not data:
        raise HTTPException(status_code=500, detail="Failed to search movies")
    
    # Also try keyword search for more relevance
    keyword_results = []
    if parsed["keywords"]:
        search_data = tmdb_request("/search/movie", {"query": parsed["keywords"][0]})
        if search_data and search_data.get("results"):
            keyword_results = search_data["results"][:5]
    
    # Combine and deduplicate results
    all_movies = data.get("results", [])
    seen_ids = {m["id"] for m in all_movies}
    for km in keyword_results:
        if km["id"] not in seen_ids:
            all_movies.insert(0, km)  # Prioritize keyword matches
            seen_ids.add(km["id"])
    
    # Enhance with vibe tags and scores
    enhanced_movies = []
    for movie in all_movies[:20]:
        genre_ids = movie.get("genre_ids", [])
        genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
        
        # Calculate a relevance score based on genre match
        matched_genre_count = len(set(genre_ids) & set(parsed["genres"]))
        relevance_score = min(70 + (matched_genre_count * 10) + int(movie.get("vote_average", 0) * 2), 100)
        
        enhanced_movies.append({
            **movie,
            "match_percentage": relevance_score,
            "vibe_tag": generate_feeling_vibe_tag(request.query, movie),
            "genres": genres,
            "poster_url": get_image_url(movie.get("poster_path"), "w500"),
            "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
        })
    
    # Sort by relevance
    enhanced_movies.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    return {
        "results": enhanced_movies,
        "query": request.query,
        "parsed_feelings": parsed,
        "page": data.get("page", 1),
        "total_pages": data.get("total_pages", 1),
    }

@api_router.get("/genres")
async def get_genre_list():
    """Get list of all genres"""
    data = tmdb_request("/genre/movie/list", ttl=86400)
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch genres")
    return data

# Seed initial watch history
@api_router.post("/seed-data")
async def seed_initial_data():
    """Seed mock user and watch history for default recommendations"""
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    
    if not user:
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "username": "flick_user",
            "birth_year": 1995,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    
    user_id = user["id"]
    
    existing_count = await db.watch_history.count_documents({"user_id": user_id})
    if existing_count >= 10:
        return {"message": "Data already seeded", "count": existing_count}
    
    mock_movies = [
        {"tmdb_id": 278, "user_rating": 10, "title": "The Shawshank Redemption", "days_ago": 400},
        {"tmdb_id": 238, "user_rating": 9, "title": "The Godfather", "days_ago": 500},
        {"tmdb_id": 155, "user_rating": 9, "title": "The Dark Knight", "days_ago": 380},
        {"tmdb_id": 550, "user_rating": 8, "title": "Fight Club", "days_ago": 450},
        {"tmdb_id": 680, "user_rating": 8, "title": "Pulp Fiction", "days_ago": 420},
        {"tmdb_id": 862, "user_rating": 6, "title": "Toy Story", "days_ago": 200},
        {"tmdb_id": 13, "user_rating": 5, "title": "Forrest Gump", "days_ago": 150},
        {"tmdb_id": 637, "user_rating": 5, "title": "Life Is Beautiful", "days_ago": 180},
        {"tmdb_id": 11, "user_rating": 4, "title": "Star Wars", "days_ago": 90},
        {"tmdb_id": 105, "user_rating": 4, "title": "Back to the Future", "days_ago": 60},
    ]
    
    for movie in mock_movies:
        details = tmdb_request(f"/movie/{movie['tmdb_id']}")
        poster_path = details.get("poster_path") if details else None
        watch_date = (datetime.now(timezone.utc) - timedelta(days=movie["days_ago"])).strftime("%Y-%m-%d")
        
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "tmdb_id": movie["tmdb_id"],
            "user_rating": float(movie["user_rating"]),
            "watch_dates": [watch_date],
            "last_watched_date": watch_date,
            "watch_count": 1,
            "title": movie["title"],
            "poster_path": poster_path
        }
        
        await db.watch_history.update_one(
            {"user_id": user_id, "tmdb_id": movie["tmdb_id"]},
            {"$set": doc},
            upsert=True
        )
    
    return {"message": "Data seeded successfully", "count": 10}

# Include the router in the main app
app.include_router(api_router)

# Serve uploaded avatar files
@app.get("/api/uploads/avatars/{filename}")
async def serve_avatar(filename: str):
    filepath = f"/app/uploads/avatars/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize genre map on startup"""
    global GENRE_MAP
    GENRE_MAP = get_genres()
    logger.info("Chef API started, genre map loaded")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
