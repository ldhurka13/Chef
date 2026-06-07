"""
Helper utilities - vibe tags, match reasons, misc helpers.
"""
from typing import List
from services.tmdb_service import FEEL_GOOD_GENRES, INTENSE_GENRES


def generate_vibe_tag(genres: List[str], vibe_params, match: int) -> str:
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


def get_match_reason(source: str, genre_match: float, director_match: float, actor_match: float, in_watchlist: bool) -> str:
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


def get_explore_match_reason(source: str, genre_match: float, director_match: float, actor_match: float) -> str:
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


# Genre groupings for movie game dissimilarity
GENRE_VIBES = {
    "light": [35, 16, 10751, 10402, 10749],  # Comedy, Animation, Family, Music, Romance
    "dark": [27, 53, 80, 9648],  # Horror, Thriller, Crime, Mystery
    "action": [28, 12, 10752, 878],  # Action, Adventure, War, Sci-Fi
    "drama": [18, 36, 10770],  # Drama, History, TV Movie
    "documentary": [99, 10402]  # Documentary, Music
}


def get_movie_vibe(genre_ids: list) -> str:
    """Determine a movie's vibe category"""
    vibe_scores = {vibe: 0 for vibe in GENRE_VIBES}
    for gid in genre_ids:
        for vibe, genres in GENRE_VIBES.items():
            if gid in genres:
                vibe_scores[vibe] += 1
    return max(vibe_scores, key=vibe_scores.get) if any(vibe_scores.values()) else "mixed"


# Feeling search mappings
FEELING_MAPPINGS = {
    "happy": {"genres": [35, 16, 10751], "keywords": ["comedy", "funny", "happy", "cheerful"]},
    "sad": {"genres": [18, 10749], "keywords": ["drama", "emotional", "tearjerker", "sad"]},
    "scared": {"genres": [27, 53], "keywords": ["horror", "scary", "thriller", "creepy"]},
    "adventurous": {"genres": [28, 12, 878], "keywords": ["adventure", "action", "exciting", "epic"]},
    "romantic": {"genres": [10749], "keywords": ["romance", "love", "romantic", "date"]},
    "thoughtful": {"genres": [99, 18, 36], "keywords": ["documentary", "thought-provoking", "deep", "mind"]},
    "nostalgic": {"genres": [10751, 16], "keywords": ["classic", "nostalgic", "childhood", "retro"]},
    "relaxed": {"genres": [35, 10751, 16], "keywords": ["relax", "chill", "cozy", "light"]},
    "thrilling": {"genres": [28, 53, 80], "keywords": ["thriller", "suspense", "exciting", "intense"]},
    "inspirational": {"genres": [18, 36], "keywords": ["inspiring", "motivational", "uplifting"]},
}


def parse_feeling_query(query: str) -> dict:
    """Parse user's feeling query and extract relevant genres and keywords"""
    query_lower = query.lower()
    matched_genres = set()
    matched_keywords = []
    
    # Check for feeling matches
    for feeling, mapping in FEELING_MAPPINGS.items():
        for keyword in mapping["keywords"]:
            if keyword in query_lower:
                matched_genres.update(mapping["genres"])
                matched_keywords.append(keyword)
    
    return {
        "genres": list(matched_genres),
        "keywords": matched_keywords,
        "original_query": query
    }


def generate_feeling_vibe_tag(query: str, movie: dict) -> str:
    """Generate a vibe tag based on feeling search query"""
    query_lower = query.lower()
    genre_ids = movie.get("genre_ids", [])
    
    if "happy" in query_lower or "funny" in query_lower:
        return "Guaranteed to lift your spirits"
    if "sad" in query_lower or "cry" in query_lower:
        return "Bring the tissues"
    if "scared" in query_lower or "horror" in query_lower:
        return "Sleep with the lights on"
    if "adventure" in query_lower or "action" in query_lower:
        return "Buckle up for excitement"
    if "romantic" in query_lower or "love" in query_lower:
        return "Perfect for date night"
    if "relax" in query_lower or "chill" in query_lower:
        return "Cozy viewing ahead"
    if "think" in query_lower or "deep" in query_lower:
        return "Food for thought"
    
    return "Matches your mood"
