from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Header, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import requests
import time
import json
import hashlib
import secrets

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

class LocationPermissionUpdate(BaseModel):
    location_permission: str  # "always", "ask", "never"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

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
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
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

@api_router.post("/auth/import-letterboxd")
async def import_letterboxd(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Import Letterboxd CSV data"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    contents = await file.read()
    if len(contents) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 1MB")
    
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = contents.decode("latin-1")
    
    import csv
    import io
    
    reader = csv.DictReader(io.StringIO(text))
    entries = []
    
    for row in reader:
        entry = {}
        # Core fields from Letterboxd format
        if row.get("Title"):
            entry["title"] = row["Title"].strip()
        elif row.get("Name"):
            entry["title"] = row["Name"].strip()
        else:
            continue
        
        if row.get("Year"):
            try:
                entry["year"] = int(row["Year"])
            except (ValueError, TypeError):
                pass
        
        # Rating (Letterboxd uses 0.5-5 scale)
        if row.get("Rating"):
            try:
                rating_5 = float(row["Rating"])
                entry["rating_5"] = rating_5
                entry["rating_10"] = int(rating_5 * 2)
            except (ValueError, TypeError):
                pass
        
        # Rating10 (1-10 scale)
        if row.get("Rating10"):
            try:
                entry["rating_10"] = int(row["Rating10"])
                entry["rating_5"] = float(row["Rating10"]) / 2
            except (ValueError, TypeError):
                pass
        
        if row.get("WatchedDate"):
            entry["watched_date"] = row["WatchedDate"].strip()
        
        if row.get("Rewatch"):
            entry["rewatch"] = row["Rewatch"].strip().lower() == "true"
        
        if row.get("Tags"):
            entry["tags"] = [t.strip() for t in row["Tags"].split(",")]
        
        if row.get("Review"):
            entry["review"] = row["Review"].strip()[:500]
        
        if row.get("tmdbID"):
            try:
                entry["tmdb_id"] = int(row["tmdbID"])
            except (ValueError, TypeError):
                pass
        
        if row.get("imdbID"):
            entry["imdb_id"] = row["imdbID"].strip()
        
        if row.get("LetterboxdURI") or row.get("url"):
            entry["letterboxd_uri"] = (row.get("LetterboxdURI") or row.get("url", "")).strip()
        
        entries.append(entry)
    
    if not entries:
        raise HTTPException(status_code=400, detail="No valid entries found in CSV")
    
    # Store in MongoDB
    import_doc = {
        "user_id": current_user["id"],
        "entries": entries,
        "total_movies": len(entries),
        "rated_movies": sum(1 for e in entries if e.get("rating_5") or e.get("rating_10")),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "filename": file.filename
    }
    
    # Upsert — replace previous import for this user
    await db.letterboxd_imports.update_one(
        {"user_id": current_user["id"]},
        {"$set": import_doc},
        upsert=True
    )
    
    # Update user flag
    await db.auth_users.update_one(
        {"id": current_user["id"]},
        {"$set": {"letterboxd_connected": True, "letterboxd_count": len(entries)}}
    )
    
    return {
        "message": f"Successfully imported {len(entries)} movies from Letterboxd",
        "total": len(entries),
        "rated": sum(1 for e in entries if e.get("rating_5") or e.get("rating_10")),
        "sample": entries[:3]
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
    """Search TMDB for movies (for favorite movie picker)"""
    if not query or len(query) < 2:
        return {"results": []}
    
    data = tmdb_request("/search/movie", {"query": query, "language": "en-US", "page": 1})
    if not data:
        return {"results": []}
    
    results = []
    for movie in data.get("results", [])[:8]:
        results.append({
            "id": movie["id"],
            "title": movie.get("title", ""),
            "year": movie.get("release_date", "")[:4] if movie.get("release_date") else "",
            "poster_url": get_image_url(movie.get("poster_path"), "w185"),
            "rating": round(movie.get("vote_average", 0), 1)
        })
    
    return {"results": results}

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
    
    return history

@api_router.post("/user/watch-history")
async def add_to_watch_history(item: WatchHistoryCreate, current_user: dict = Depends(get_current_user)):
    """Add movie to authenticated user's watch history"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    watched_date = item.watched_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Check if already in history
    existing = await db.watch_history.find_one(
        {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
        {"_id": 0}
    )
    
    if existing:
        # Append new watch date and update rating
        watch_dates = existing.get("watch_dates", [])
        if watched_date not in watch_dates:
            watch_dates.append(watched_date)
        watch_dates.sort(reverse=True)
        
        await db.watch_history.update_one(
            {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
            {
                "$set": {
                    "user_rating": item.user_rating,
                    "last_watched_date": watch_dates[0],
                    "watch_dates": watch_dates,
                    "watch_count": len(watch_dates),
                    "title": item.title or existing.get("title", ""),
                    "poster_path": item.poster_path or existing.get("poster_path")
                }
            }
        )
        updated = await db.watch_history.find_one(
            {"user_id": current_user["id"], "tmdb_id": item.tmdb_id},
            {"_id": 0}
        )
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
        "title": item.title,
        "poster_path": item.poster_path
    }
    await db.watch_history.insert_one(doc)
    doc.pop("_id", None)
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
