"""
Scoring utilities - complexity, nostalgia, rewatchability calculations.
"""
from typing import List, Optional
from datetime import datetime, timezone
from services.tmdb_service import (
    GENRE_COMPLEXITY, 
    LOW_ENERGY_GENRES, 
    HIGH_ENERGY_GENRES,
    FEEL_GOOD_GENRES,
    INTENSE_GENRES,
    get_genre_map,
    get_image_url
)
from database import db


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
    GENRE_MAP = get_genre_map()
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
    vibe_params
) -> dict:
    """
    Main scoring function:
    1. Base Score: TMDB average rating
    2. Rewatchability Multiplier
    3. Energy-based Complexity Penalty
    4. Mood adjustment
    """
    from utils.helpers import generate_vibe_tag
    
    GENRE_MAP = get_genre_map()
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
