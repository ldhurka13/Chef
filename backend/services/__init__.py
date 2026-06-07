"""
Services for the Chef application.
"""
from services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
    get_current_user,
)
from services.tmdb_service import (
    tmdb_request,
    get_image_url,
    get_genres,
    load_genre_map,
    get_genre_map,
    GENRE_MAP,
    LOW_ENERGY_GENRES,
    HIGH_ENERGY_GENRES,
    FEEL_GOOD_GENRES,
    INTENSE_GENRES,
    GENRE_COMPLEXITY,
)
from services.weather import (
    fetch_weather,
    get_weather_description,
    generate_comfort_vibe_tag,
)
from services.streaming import (
    fetch_streaming_availability,
    get_cached_streaming,
    SERVICE_DISPLAY,
)

__all__ = [
    # Auth
    "hash_password",
    "verify_password",
    "create_token",
    "verify_token",
    "get_current_user",
    # TMDB
    "tmdb_request",
    "get_image_url",
    "get_genres",
    "load_genre_map",
    "get_genre_map",
    "GENRE_MAP",
    "LOW_ENERGY_GENRES",
    "HIGH_ENERGY_GENRES",
    "FEEL_GOOD_GENRES",
    "INTENSE_GENRES",
    "GENRE_COMPLEXITY",
    # Weather
    "fetch_weather",
    "get_weather_description",
    "generate_comfort_vibe_tag",
    # Streaming
    "fetch_streaming_availability",
    "get_cached_streaming",
    "SERVICE_DISPLAY",
]
