"""
Watch history related Pydantic models.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid


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
