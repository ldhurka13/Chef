"""
Onboarding router - eligibility and dismissal endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from services.auth_service import get_current_user
from services.onboarding_service import (
    get_onboarding_eligibility,
    mark_onboarding_skipped,
    mark_onboarding_completed
)
from services.tmdb_service import tmdb_request
from models.onboarding import OnboardingStatus, OnboardingDismissRequest

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/eligibility", response_model=OnboardingStatus)
async def check_onboarding_eligibility(current_user: dict = Depends(get_current_user)):
    """
    Check if the current user is eligible for starter library onboarding.
    
    Returns:
    - eligible: True if user has < 5 diary entries (minimum required for personalization)
    - diary_count: Number of entries in user's diary
    - watchlist_count: Number of entries in user's watchlist
    - onboarding_skipped: Whether user previously skipped onboarding
    - onboarding_completed: Whether user completed onboarding by adding items
    - minimum_required: Minimum diary entries needed (5)
    - movies_needed: How many more movies user needs to add
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await get_onboarding_eligibility(current_user["id"])
    return OnboardingStatus(**result)


@router.get("/popular-movies")
async def get_popular_movies_for_onboarding():
    """
    Get popular movies from TMDB for onboarding.
    Returns a mix of all-time popular and classic films.
    """
    try:
        all_movies = []
        
        # Get popular movies from multiple pages for variety
        for page in range(1, 4):  # 3 pages = ~60 movies
            data = tmdb_request("/movie/popular", {"page": page})
            if data and data.get("results"):
                all_movies.extend(data["results"])
        
        # Also get some top-rated classics
        top_rated = tmdb_request("/movie/top_rated", {"page": 1})
        if top_rated and top_rated.get("results"):
            all_movies.extend(top_rated["results"])
        
        # Deduplicate by id
        seen_ids = set()
        unique_movies = []
        for movie in all_movies:
            if movie.get("id") not in seen_ids:
                seen_ids.add(movie["id"])
                # Add full poster URL for convenience
                poster_path = movie.get("poster_path")
                if poster_path:
                    movie["poster_url"] = f"https://image.tmdb.org/t/p/w185{poster_path}"
                unique_movies.append(movie)
        
        # Shuffle for variety but keep popular ones weighted toward front
        import random
        # Take first 20 popular, then shuffle rest and add some
        popular_batch = unique_movies[:20]
        rest = unique_movies[20:]
        random.shuffle(rest)
        
        # Combine: 20 popular + 10 random from rest
        final_movies = popular_batch + rest[:10]
        
        return {"results": final_movies[:30]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch popular movies: {str(e)}")


@router.post("/skip")
async def skip_onboarding(
    request: OnboardingDismissRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark that the user skipped/dismissed the onboarding modal.
    This persists the dismissal but doesn't prevent re-prompting
    if the user still has less than 5 diary entries.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await mark_onboarding_skipped(current_user["id"])
    return result


@router.post("/complete")
async def complete_onboarding(current_user: dict = Depends(get_current_user)):
    """
    Mark that the user completed onboarding by adding items.
    Called after user adds their first item via the onboarding flow.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await mark_onboarding_completed(current_user["id"])
    return result
