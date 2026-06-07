"""
Watchlist related Pydantic models.
"""
from pydantic import BaseModel
from typing import List, Optional


class WatchlistAdd(BaseModel):
    tmdb_id: int
    title: str = ""
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    genres: Optional[List[str]] = None
