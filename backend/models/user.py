"""
User-related Pydantic models.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    birth_year: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    favorite_directors: Optional[List[str]] = None


class LocationPermissionUpdate(BaseModel):
    location_permission: str  # "always", "ask", "never"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
