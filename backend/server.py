from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import requests
import time
import json

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

# Cache for TMDB requests
tmdb_cache = {}
CACHE_TTL = 3600  # 1 hour

# Create the main app
app = FastAPI(title="Flick - Movie Recommendation Engine")

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
    user_rating: int = Field(ge=1, le=10)
    last_watched_date: datetime
    watch_count: int = 1
    title: str = ""
    poster_path: Optional[str] = None

class WatchHistoryCreate(BaseModel):
    tmdb_id: int
    user_rating: int = Field(ge=1, le=10)
    title: str = ""
    poster_path: Optional[str] = None

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
    return {"message": "Flick - Context-Aware Movie Recommendations"}

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
async def get_watch_history():
    """Get user's watch history"""
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    if not user:
        return []
    
    history = await db.watch_history.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("last_watched_date", -1).to_list(100)
    
    return history

@api_router.post("/user/watch-history")
async def add_to_watch_history(item: WatchHistoryCreate):
    """Add movie to watch history"""
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already in history
    existing = await db.watch_history.find_one(
        {"user_id": user["id"], "tmdb_id": item.tmdb_id},
        {"_id": 0}
    )
    
    if existing:
        # Update existing entry
        await db.watch_history.update_one(
            {"user_id": user["id"], "tmdb_id": item.tmdb_id},
            {
                "$set": {
                    "user_rating": item.user_rating,
                    "last_watched_date": datetime.now(timezone.utc).isoformat(),
                    "title": item.title,
                    "poster_path": item.poster_path
                },
                "$inc": {"watch_count": 1}
            }
        )
        updated = await db.watch_history.find_one(
            {"user_id": user["id"], "tmdb_id": item.tmdb_id},
            {"_id": 0}
        )
        return updated
    
    # Create new entry
    watch_item = WatchHistoryItem(
        user_id=user["id"],
        tmdb_id=item.tmdb_id,
        user_rating=item.user_rating,
        last_watched_date=datetime.now(timezone.utc),
        title=item.title,
        poster_path=item.poster_path
    )
    
    doc = watch_item.model_dump()
    doc['last_watched_date'] = doc['last_watched_date'].isoformat()
    await db.watch_history.insert_one(doc)
    
    return doc

@api_router.delete("/user/watch-history/{tmdb_id}")
async def remove_from_watch_history(tmdb_id: int):
    """Remove movie from watch history"""
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.watch_history.delete_one(
        {"user_id": user["id"], "tmdb_id": tmdb_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Movie not in watch history")
    
    return {"message": "Removed from watch history"}

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
        ]
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
    """Seed mock user and watch history"""
    # Create or get user
    user = await db.users.find_one({"username": "flick_user"}, {"_id": 0})
    
    if not user:
        mock_user = User(username="flick_user", birth_year=1995)
        doc = mock_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        user = doc
    
    user_id = user["id"]
    
    # Check if history already seeded
    existing_count = await db.watch_history.count_documents({"user_id": user_id})
    if existing_count >= 10:
        return {"message": "Data already seeded", "count": existing_count}
    
    # Mock watch history: 10 classic movies (5 high rated, 5 lower rated)
    mock_movies = [
        # High rated (8-10)
        {"tmdb_id": 278, "user_rating": 10, "title": "The Shawshank Redemption", "days_ago": 400},
        {"tmdb_id": 238, "user_rating": 9, "title": "The Godfather", "days_ago": 500},
        {"tmdb_id": 155, "user_rating": 9, "title": "The Dark Knight", "days_ago": 380},
        {"tmdb_id": 550, "user_rating": 8, "title": "Fight Club", "days_ago": 450},
        {"tmdb_id": 680, "user_rating": 8, "title": "Pulp Fiction", "days_ago": 420},
        # Lower rated (4-6)
        {"tmdb_id": 862, "user_rating": 6, "title": "Toy Story", "days_ago": 200},
        {"tmdb_id": 13, "user_rating": 5, "title": "Forrest Gump", "days_ago": 150},
        {"tmdb_id": 637, "user_rating": 5, "title": "Life Is Beautiful", "days_ago": 180},
        {"tmdb_id": 11, "user_rating": 4, "title": "Star Wars", "days_ago": 90},
        {"tmdb_id": 105, "user_rating": 4, "title": "Back to the Future", "days_ago": 60},
    ]
    
    for movie in mock_movies:
        # Get poster from TMDB
        details = tmdb_request(f"/movie/{movie['tmdb_id']}")
        poster_path = details.get("poster_path") if details else None
        
        watch_date = datetime.now(timezone.utc) - timedelta(days=movie["days_ago"])
        
        watch_item = WatchHistoryItem(
            user_id=user_id,
            tmdb_id=movie["tmdb_id"],
            user_rating=movie["user_rating"],
            last_watched_date=watch_date,
            title=movie["title"],
            poster_path=poster_path
        )
        
        doc = watch_item.model_dump()
        doc['last_watched_date'] = doc['last_watched_date'].isoformat()
        
        # Upsert to avoid duplicates
        await db.watch_history.update_one(
            {"user_id": user_id, "tmdb_id": movie["tmdb_id"]},
            {"$set": doc},
            upsert=True
        )
    
    return {"message": "Data seeded successfully", "count": 10}

# Include the router in the main app
app.include_router(api_router)

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
    logger.info("Flick API started, genre map loaded")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
