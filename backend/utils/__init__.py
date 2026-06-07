"""
Utility functions for the Chef application.
"""
from utils.scoring import (
    calculate_complexity_score,
    calculate_nostalgia_bonus,
    calculate_complexity_penalty,
    calculate_rewatchability_multiplier,
    calculate_flick_score,
)
from utils.helpers import (
    generate_vibe_tag,
    get_match_reason,
    get_explore_match_reason,
    get_movie_vibe,
    GENRE_VIBES,
    FEELING_MAPPINGS,
    parse_feeling_query,
    generate_feeling_vibe_tag,
)

__all__ = [
    # Scoring
    "calculate_complexity_score",
    "calculate_nostalgia_bonus",
    "calculate_complexity_penalty",
    "calculate_rewatchability_multiplier",
    "calculate_flick_score",
    # Helpers
    "generate_vibe_tag",
    "get_match_reason",
    "get_explore_match_reason",
    "get_movie_vibe",
    "GENRE_VIBES",
    "FEELING_MAPPINGS",
    "parse_feeling_query",
    "generate_feeling_vibe_tag",
]
