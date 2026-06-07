"""
Movie-related Pydantic models.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


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


class AIVibeRequest(BaseModel):
    brain_power: int = Field(ge=0, le=100, default=50)
    mood: int = Field(ge=0, le=100, default=50)  # 0=Serious (dramatic), 100=Fun (comedy)
    energy: int = Field(ge=0, le=100, default=50)  # 0=Exhausted (calming), 100=LFG (intense)
    watch_context: str = Field(default="solo")  # "solo", "date", "group"


class ComfortRequest(BaseModel):
    hour: int = 12  # Hour of day (0-23)
    is_cold: bool = False  # Weather condition
    is_rainy: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FeelingSearchRequest(BaseModel):
    query: str
    page: int = 1
