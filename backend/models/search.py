"""
Search-related Pydantic models for unified search functionality.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SearchSuggestionTitle(BaseModel):
    """Normalized title result (movie or TV show)"""
    id: int
    media_type: str = Field(description="'movie' or 'tv'")
    title: str
    year: Optional[str] = None
    poster_path: Optional[str] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None
    vote_average: Optional[float] = None


class SearchSuggestionPerson(BaseModel):
    """Normalized person result (actor/director)"""
    id: int
    name: str
    profile_path: Optional[str] = None
    profile_url: Optional[str] = None
    known_for_department: Optional[str] = None
    known_for: Optional[str] = None  # Concise known-for label


class UnifiedSearchResponse(BaseModel):
    """Response for unified search suggestions"""
    titles: List[SearchSuggestionTitle] = []
    people: List[SearchSuggestionPerson] = []
    query: str


class PersonCreditsResponse(BaseModel):
    """Response for person credits"""
    id: int
    name: str
    profile_path: Optional[str] = None
    profile_url: Optional[str] = None
    known_for_department: Optional[str] = None
    biography: Optional[str] = None
    birthday: Optional[str] = None
    place_of_birth: Optional[str] = None
    acting: List[dict] = []  # Movie/TV credits as actor
    directing: List[dict] = []  # Movie/TV credits as director


class VibeSearchRequest(BaseModel):
    """Request for free-text vibe search (extends AIVibeRequest behavior)"""
    query: str = Field(description="Free-text mood/vibe query")
    limit: int = Field(default=5, ge=1, le=20, description="Number of results to return")
