"""
Search router - unified search suggestions, person credits, and free-text vibe search.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
import os
import json
import time

from services.search_service import (
    get_unified_suggestions,
    get_person_credits,
    is_likely_entity_search
)
from services.tmdb_service import tmdb_request, get_image_url
from models.search import (
    UnifiedSearchResponse,
    PersonCreditsResponse,
    VibeSearchRequest
)
from services.auth_service import get_current_user_optional
from database import db

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/suggestions", response_model=UnifiedSearchResponse)
async def search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=8, ge=1, le=15, description="Max results")
):
    """
    Get unified search suggestions for the dropdown.
    Returns normalized movie/TV titles and person results.
    
    Debounced on frontend (250-350ms).
    """
    try:
        results = get_unified_suggestions(q, max_results=limit)
        return UnifiedSearchResponse(
            titles=results.get("titles", []),
            people=results.get("people", []),
            query=q
        )
    except Exception as e:
        logging.error(f"Search suggestions failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/person/{person_id}")
async def get_person_details(person_id: int):
    """
    Get person details and credits (acting + directing).
    """
    try:
        result = get_person_credits(person_id)
        if not result:
            raise HTTPException(status_code=404, detail="Person not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Person credits failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch person details")


@router.get("/intent")
async def check_search_intent(q: str = Query(..., min_length=2)):
    """
    Check if a query is likely an entity search or a vibe/mood search.
    Used by frontend to determine whether to open entity or run AI vibe search.
    
    Returns:
    - is_entity: True if query matches a title/person
    - best_match: The best matching entity if is_entity is True
    """
    try:
        suggestions = get_unified_suggestions(q, max_results=5)
        is_entity = is_likely_entity_search(q, suggestions)
        
        best_match = None
        if is_entity:
            # Return the best match
            if suggestions.get("titles"):
                best_match = {
                    "type": "title",
                    "data": suggestions["titles"][0]
                }
            elif suggestions.get("people"):
                best_match = {
                    "type": "person", 
                    "data": suggestions["people"][0]
                }
        
        return {
            "is_entity": is_entity,
            "best_match": best_match,
            "query": q
        }
    except Exception as e:
        logging.error(f"Intent check failed: {e}")
        # Default to vibe search on error
        return {
            "is_entity": False,
            "best_match": None,
            "query": q
        }



# Lazy load GENRE_MAP
GENRE_MAP = None

def get_genres():
    """Get genre ID to name mapping from TMDB"""
    data = tmdb_request("/genre/movie/list", ttl=86400)
    if data and "genres" in data:
        return {g["id"]: g["name"] for g in data["genres"]}
    return {}


@router.post("/vibe")
async def free_text_vibe_search(
    request: VibeSearchRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Free-text vibe/mood search using the AI Vibe Engine.
    Returns exactly 5 movie recommendations based on the natural language query.
    
    This reuses the existing AI Vibe Engine logic but accepts a free-text query
    instead of slider parameters.
    """
    global GENRE_MAP
    if not GENRE_MAP:
        GENRE_MAP = get_genres()
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    user_id = current_user.get("id") if current_user else None
    query = request.query.strip()
    limit = min(request.limit, 5)  # Cap at 5 for unified search
    
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    # Build user profile context for personalization
    user_profile = {
        "age": None,
        "top_genres": [],
        "top_actors": [],
        "top_directors": [],
        "watch_history": []
    }
    
    if user_id:
        # Get user data
        user_data = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user_data:
            from datetime import datetime
            birth_year = user_data.get("birth_year", 1995)
            user_profile["age"] = datetime.now().year - birth_year
            user_profile["top_genres"] = user_data.get("favorite_genres", [])
            user_profile["top_actors"] = user_data.get("favorite_actors", [])
            user_profile["top_directors"] = user_data.get("favorite_directors", [])
        
        # Get watch history (last 30 movies for exclusion)
        watch_history = await db.watch_history.find(
            {"user_id": user_id},
            {"_id": 0, "title": 1, "user_rating": 1, "tmdb_id": 1}
        ).sort("last_watched_date", -1).to_list(30)
        
        user_profile["watch_history"] = [
            {"title": w.get("title", ""), "rating": w.get("user_rating", 0)}
            for w in watch_history
        ]
        
        # Try to get profile insights for better recommendations
        insights_cache = await db.user_insights_cache.find_one(
            {"user_id": user_id},
            {"_id": 0, "top_genres": 1, "top_directors": 1, "top_actors": 1}
        )
        if insights_cache:
            if not user_profile["top_genres"] and insights_cache.get("top_genres"):
                user_profile["top_genres"] = [g["name"] for g in insights_cache["top_genres"][:3]]
            if not user_profile["top_directors"] and insights_cache.get("top_directors"):
                user_profile["top_directors"] = [d["name"] for d in insights_cache["top_directors"][:3]]
            if not user_profile["top_actors"] and insights_cache.get("top_actors"):
                user_profile["top_actors"] = [a["name"] for a in insights_cache["top_actors"][:3]]
    
    # Build watch history exclusion text
    watch_history_text = ""
    watched_titles = [w["title"] for w in user_profile["watch_history"] if w["title"]]
    if watched_titles:
        watch_history_text = f"\n\nUser's recent watch history (try to AVOID these unless they're perfect matches): {', '.join(watched_titles[:20])}"
    
    # Build profile context
    profile_text = ""
    if user_profile["top_genres"]:
        profile_text += f"\nUser likes these genres: {', '.join(user_profile['top_genres'])}"
    if user_profile["top_directors"]:
        profile_text += f"\nFavorite directors: {', '.join(user_profile['top_directors'])}"
    if user_profile["top_actors"]:
        profile_text += f"\nFavorite actors: {', '.join(user_profile['top_actors'])}"
    
    system_prompt = f"""You are Chef, an expert movie recommendation AI. 
Your task is to recommend exactly {limit} movies based on the user's mood, feeling, or activity description.

IMPORTANT GUIDELINES:
1. Interpret the user's natural language description to understand their mood and what kind of movie experience they want
2. Return exactly {limit} movies that match their vibe
3. Prioritize quality and relevance over popularity
4. Include a mix of well-known films and hidden gems
5. Each movie must be searchable on TMDB
6. Provide a brief, personalized reason why each movie matches their mood

Return ONLY a valid JSON array with exactly {limit} movies:
[
  {{"title": "Movie Name", "year": "YYYY", "vibe_score": 95, "reason": "Why this matches their mood (max 15 words)"}},
  ...
]"""

    user_prompt = f"""Find {limit} perfect movies for someone who says: "{query}"
{profile_text}
{watch_history_text}

Return exactly {limit} movie recommendations as a JSON array with title, year, vibe_score (0-100), and reason fields."""

    try:
        # Initialize LLM chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"vibe-search-{user_id or 'anon'}-{int(time.time())}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=user_prompt)
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        response_text = response.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        ai_recommendations = json.loads(response_text)
        
        if not isinstance(ai_recommendations, list) or len(ai_recommendations) == 0:
            raise ValueError("Invalid AI response format")
        
    except Exception as e:
        logging.error(f"AI vibe search failed: {e}")
        raise HTTPException(status_code=500, detail="AI recommendation failed. Please try again.")
    
    # Enrich recommendations with TMDB data
    enriched_results = []
    seen_ids = set()
    
    for rec in ai_recommendations[:limit]:
        title = rec.get("title", "")
        year = rec.get("year", "")
        reason = rec.get("reason", "")
        vibe_score = rec.get("vibe_score", 80)
        
        # Search TMDB for the movie
        search_params = {"query": title}
        if year and year.isdigit():
            search_params["year"] = year
        
        search_data = tmdb_request("/search/movie", search_params)
        
        if search_data and search_data.get("results"):
            movie = search_data["results"][0]
            movie_id = movie.get("id")
            
            # Skip duplicates
            if movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            
            genre_ids = movie.get("genre_ids", [])
            genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
            
            enriched_results.append({
                "id": movie_id,
                "media_type": "movie",
                "title": movie.get("title", title),
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
                "overview": movie.get("overview", ""),
                "release_date": movie.get("release_date", ""),
                "vote_average": movie.get("vote_average", 0),
                "genres": genres,
                "vibe_reason": reason,
                "vibe_score": vibe_score,
                "ai_recommended": True,
                "poster_url": get_image_url(movie.get("poster_path"), "w500"),
                "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
            })
    
    # If we don't have enough results, try fallback
    if len(enriched_results) < limit:
        # Try a simple TMDB discover as fallback
        fallback_data = tmdb_request("/discover/movie", {
            "sort_by": "popularity.desc",
            "vote_count.gte": 100,
            "page": 1
        })
        if fallback_data and fallback_data.get("results"):
            for movie in fallback_data["results"]:
                if len(enriched_results) >= limit:
                    break
                movie_id = movie.get("id")
                if movie_id not in seen_ids:
                    seen_ids.add(movie_id)
                    genre_ids = movie.get("genre_ids", [])
                    genres = [GENRE_MAP.get(gid, "") for gid in genre_ids if gid in GENRE_MAP]
                    enriched_results.append({
                        "id": movie_id,
                        "media_type": "movie",
                        "title": movie.get("title", ""),
                        "poster_path": movie.get("poster_path"),
                        "backdrop_path": movie.get("backdrop_path"),
                        "overview": movie.get("overview", ""),
                        "release_date": movie.get("release_date", ""),
                        "vote_average": movie.get("vote_average", 0),
                        "genres": genres,
                        "vibe_reason": "Popular pick that might match your mood",
                        "vibe_score": 60,
                        "ai_recommended": False,
                        "poster_url": get_image_url(movie.get("poster_path"), "w500"),
                        "backdrop_url": get_image_url(movie.get("backdrop_path"), "w1280"),
                    })
    
    return {
        "results": enriched_results[:limit],
        "query": query,
        "ai_powered": True
    }
