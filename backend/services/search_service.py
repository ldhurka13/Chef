"""
Search service - TMDB multi-search, person credits, and unified search orchestration.
Uses tmdb_service.py for actual TMDB requests.
"""
import logging
from typing import Optional, Dict, List, Set
from services.tmdb_service import tmdb_request, get_image_url


def normalize_title_result(item: dict, media_type: str) -> dict:
    """Normalize a movie or TV result to a consistent shape."""
    if media_type == "movie":
        title = item.get("title", "")
        release_date = item.get("release_date", "")
        year = release_date[:4] if release_date else None
    else:  # TV
        title = item.get("name", "")
        first_air_date = item.get("first_air_date", "")
        year = first_air_date[:4] if first_air_date else None
    
    poster_path = item.get("poster_path")
    
    return {
        "id": item.get("id"),
        "media_type": media_type,
        "title": title,
        "year": year,
        "poster_path": poster_path,
        "poster_url": get_image_url(poster_path, "w185") if poster_path else None,
        "overview": item.get("overview", "")[:200] if item.get("overview") else None,
        "vote_average": item.get("vote_average"),
    }


def normalize_person_result(item: dict) -> dict:
    """Normalize a person result to a consistent shape."""
    profile_path = item.get("profile_path")
    known_for = item.get("known_for", [])
    
    # Build concise known-for label
    known_for_label = None
    if known_for:
        titles = []
        for kf in known_for[:2]:
            title = kf.get("title") or kf.get("name")
            if title:
                titles.append(title)
        if titles:
            known_for_label = ", ".join(titles)
    
    return {
        "id": item.get("id"),
        "name": item.get("name", ""),
        "profile_path": profile_path,
        "profile_url": get_image_url(profile_path, "w185") if profile_path else None,
        "known_for_department": item.get("known_for_department"),
        "known_for": known_for_label,
    }


def get_unified_suggestions(query: str, max_results: int = 8) -> dict:
    """
    Get unified search suggestions from TMDB multi-search.
    Returns normalized titles (movies/TV) and people results.
    """
    if not query or len(query.strip()) < 2:
        return {"titles": [], "people": [], "query": query}
    
    query = query.strip()
    
    # Use TMDB multi-search
    data = tmdb_request("/search/multi", {"query": query, "page": 1, "include_adult": False})
    
    if not data or "results" not in data:
        return {"titles": [], "people": [], "query": query}
    
    titles = []
    people = []
    seen_title_ids: Set[int] = set()
    seen_person_ids: Set[int] = set()
    
    # Independent quotas so a person-name query still surfaces people
    people_limit = min(4, max_results)
    
    for item in data.get("results", []):
        media_type = item.get("media_type")
        item_id = item.get("id")
        
        if not item_id:
            continue
        
        if media_type == "movie":
            if item_id not in seen_title_ids and len(titles) < max_results:
                titles.append(normalize_title_result(item, "movie"))
                seen_title_ids.add(item_id)
                
        elif media_type == "tv":
            if item_id not in seen_title_ids and len(titles) < max_results:
                titles.append(normalize_title_result(item, "tv"))
                seen_title_ids.add(item_id)
                
        elif media_type == "person":
            if item_id not in seen_person_ids and len(people) < people_limit:
                people.append(normalize_person_result(item))
                seen_person_ids.add(item_id)
    
    return {
        "titles": titles,
        "people": people,
        "query": query
    }


def get_person_credits(person_id: int) -> Optional[dict]:
    """
    Get person details and their combined movie/TV credits.
    Returns acting and directing credits separately.
    """
    # Get person details
    person_data = tmdb_request(f"/person/{person_id}")
    if not person_data:
        return None
    
    # Get combined credits (movies + TV)
    credits_data = tmdb_request(f"/person/{person_id}/combined_credits")
    if not credits_data:
        credits_data = {"cast": [], "crew": []}
    
    profile_path = person_data.get("profile_path")
    
    # Process acting credits
    acting_credits = []
    seen_acting: Set[str] = set()  # (id, media_type)
    
    for credit in credits_data.get("cast", []):
        media_type = credit.get("media_type", "movie")
        credit_id = credit.get("id")
        
        if not credit_id:
            continue
        
        unique_key = f"{credit_id}_{media_type}"
        if unique_key in seen_acting:
            continue
        seen_acting.add(unique_key)
        
        # Get title and year based on media type
        if media_type == "movie":
            title = credit.get("title", "")
            release_date = credit.get("release_date", "")
            year = release_date[:4] if release_date else None
        else:
            title = credit.get("name", "")
            first_air_date = credit.get("first_air_date", "")
            year = first_air_date[:4] if first_air_date else None
        
        poster_path = credit.get("poster_path")
        
        acting_credits.append({
            "id": credit_id,
            "media_type": media_type,
            "title": title,
            "year": year,
            "character": credit.get("character", ""),
            "poster_path": poster_path,
            "poster_url": get_image_url(poster_path, "w185") if poster_path else None,
            "vote_average": credit.get("vote_average"),
            "popularity": credit.get("popularity", 0),
        })
    
    # Process directing credits
    directing_credits = []
    seen_directing: Set[str] = set()
    
    for credit in credits_data.get("crew", []):
        if credit.get("job") != "Director":
            continue
        
        media_type = credit.get("media_type", "movie")
        credit_id = credit.get("id")
        
        if not credit_id:
            continue
        
        unique_key = f"{credit_id}_{media_type}"
        if unique_key in seen_directing:
            continue
        seen_directing.add(unique_key)
        
        if media_type == "movie":
            title = credit.get("title", "")
            release_date = credit.get("release_date", "")
            year = release_date[:4] if release_date else None
        else:
            title = credit.get("name", "")
            first_air_date = credit.get("first_air_date", "")
            year = first_air_date[:4] if first_air_date else None
        
        poster_path = credit.get("poster_path")
        
        directing_credits.append({
            "id": credit_id,
            "media_type": media_type,
            "title": title,
            "year": year,
            "poster_path": poster_path,
            "poster_url": get_image_url(poster_path, "w185") if poster_path else None,
            "vote_average": credit.get("vote_average"),
            "popularity": credit.get("popularity", 0),
        })
    
    # Sort by popularity and limit
    acting_credits.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    directing_credits.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    
    return {
        "id": person_data.get("id"),
        "name": person_data.get("name", ""),
        "profile_path": profile_path,
        "profile_url": get_image_url(profile_path, "w500") if profile_path else None,
        "known_for_department": person_data.get("known_for_department"),
        "biography": person_data.get("biography"),
        "birthday": person_data.get("birthday"),
        "place_of_birth": person_data.get("place_of_birth"),
        "acting": acting_credits[:50],  # Limit to 50
        "directing": directing_credits[:50],
    }


def is_likely_entity_search(query: str, suggestions: dict) -> bool:
    """
    Determine if a query is likely searching for a specific entity (title/person)
    rather than expressing a mood/vibe.
    
    Returns True if strong title/person matches exist.
    """
    query_normalized = query.lower().strip()
    
    # Check titles
    for title in suggestions.get("titles", [])[:3]:
        title_name = (title.get("title") or "").lower()
        # Exact or very close match
        if title_name == query_normalized:
            return True
        # Query is contained in title or vice versa
        if len(query_normalized) >= 3:
            if query_normalized in title_name or title_name in query_normalized:
                return True
    
    # Check people
    for person in suggestions.get("people", [])[:3]:
        person_name = (person.get("name") or "").lower()
        if person_name == query_normalized:
            return True
        # Check if query matches significant part of name
        name_parts = person_name.split()
        query_parts = query_normalized.split()
        if any(qp in name_parts for qp in query_parts if len(qp) > 2):
            return True
    
    return False
