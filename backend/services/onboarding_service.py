"""
Onboarding service - eligibility checks and dismissal logic.
"""
from database import db

# Minimum movies required before full features are unlocked
MINIMUM_DIARY_COUNT = 5


async def get_onboarding_eligibility(user_id: str) -> dict:
    """
    Check if user is eligible for starter library onboarding.
    
    User is eligible if:
    - diary_count < MINIMUM_DIARY_COUNT (5 movies minimum required)
    - AND not already completed onboarding
    
    Returns eligibility status along with counts and progress info.
    """
    # Get user's onboarding status
    user = await db.auth_users.find_one(
        {"id": user_id},
        {"_id": 0, "onboarding_skipped": 1, "onboarding_completed": 1}
    )
    
    onboarding_skipped = user.get("onboarding_skipped", False) if user else False
    onboarding_completed = user.get("onboarding_completed", False) if user else False
    
    # Count diary entries (watch_history)
    diary_count = await db.watch_history.count_documents({"user_id": user_id})
    
    # Count watchlist entries
    watchlist_count = await db.watchlist.count_documents({"user_id": user_id})
    
    # User is eligible if diary count is less than minimum required
    # This ensures users build a taste profile before accessing full features
    eligible = diary_count < MINIMUM_DIARY_COUNT
    
    # Calculate progress toward minimum
    movies_needed = max(0, MINIMUM_DIARY_COUNT - diary_count)
    
    return {
        "eligible": eligible,
        "diary_count": diary_count,
        "watchlist_count": watchlist_count,
        "onboarding_skipped": onboarding_skipped,
        "onboarding_completed": onboarding_completed,
        "minimum_required": MINIMUM_DIARY_COUNT,
        "movies_needed": movies_needed
    }


async def mark_onboarding_skipped(user_id: str) -> dict:
    """Mark that user skipped/dismissed the onboarding modal."""
    await db.auth_users.update_one(
        {"id": user_id},
        {"$set": {"onboarding_skipped": True}}
    )
    return {"success": True, "onboarding_skipped": True}


async def mark_onboarding_completed(user_id: str) -> dict:
    """Mark that user completed onboarding (added items via onboarding flow)."""
    await db.auth_users.update_one(
        {"id": user_id},
        {"$set": {"onboarding_completed": True}}
    )
    return {"success": True, "onboarding_completed": True}
