"""
Pydantic models for the Chef application.
"""
from models.user import (
    User,
    UserRegister,
    UserLogin,
    UserProfile,
    UserUpdate,
    LocationPermissionUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from models.watch_history import (
    WatchHistoryItem,
    WatchHistoryCreate,
    WatchHistoryUpdate,
    WatchEntryCreate,
    WatchEntryUpdate,
)
from models.movie import (
    MovieMetadata,
    VibeParams,
    AIVibeRequest,
    ComfortRequest,
    FeelingSearchRequest,
)
from models.watchlist import WatchlistAdd
from models.game import GameChoiceV2

__all__ = [
    # User models
    "User",
    "UserRegister",
    "UserLogin",
    "UserProfile",
    "UserUpdate",
    "LocationPermissionUpdate",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    # Watch history models
    "WatchHistoryItem",
    "WatchHistoryCreate",
    "WatchHistoryUpdate",
    "WatchEntryCreate",
    "WatchEntryUpdate",
    # Movie models
    "MovieMetadata",
    "VibeParams",
    "AIVibeRequest",
    "ComfortRequest",
    "FeelingSearchRequest",
    # Watchlist models
    "WatchlistAdd",
    # Game models
    "GameChoiceV2",
]
