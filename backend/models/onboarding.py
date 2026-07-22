"""
Onboarding-related Pydantic models.
"""
from pydantic import BaseModel
from typing import Optional


class OnboardingStatus(BaseModel):
    """Response model for onboarding eligibility check"""
    eligible: bool
    diary_count: int
    watchlist_count: int
    onboarding_skipped: bool
    onboarding_completed: bool
    minimum_required: int = 5
    movies_needed: int = 5


class OnboardingDismissRequest(BaseModel):
    """Request model for dismissing/skipping onboarding"""
    skipped: bool = True
