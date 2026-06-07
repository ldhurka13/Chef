"""
Streaming availability service - MoviesOfTheNight API integration.
"""
import logging
import requests
from datetime import datetime, timezone
from config import RAPIDAPI_KEY, STREAMING_API_BASE, ALLOWED_SERVICES
from database import db

# Service display information
SERVICE_DISPLAY = {
    "netflix": {"name": "Netflix", "color": "#E50914"},
    "prime": {"name": "Prime Video", "color": "#00A8E1"},
    "disney": {"name": "Disney+", "color": "#113CCF"},
    "hulu": {"name": "Hulu", "color": "#1CE783"},
    "apple": {"name": "Apple TV+", "color": "#A2AAAD"},
    "hbo": {"name": "Max", "color": "#002BE7"},
    "paramount": {"name": "Paramount+", "color": "#0064FF"},
}


def fetch_streaming_availability(tmdb_id: int, country: str = "us") -> list:
    """Fetch streaming availability from Movies of the Night API with MongoDB caching"""
    try:
        url = f"{STREAMING_API_BASE}/shows/movie/{tmdb_id}"
        headers = {
            "x-rapidapi-host": "streaming-availability.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        params = {"country": country}
        
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 404:
            return []
        res.raise_for_status()
        data = res.json()
        
        streaming_options = data.get("streamingOptions", {})
        country_options = streaming_options.get(country, [])
        
        # Filter to allowed services and build clean response
        results = []
        seen_services = set()
        for opt in country_options:
            svc = opt.get("service", {})
            svc_id = svc.get("id", "")
            
            if svc_id not in ALLOWED_SERVICES:
                continue
            
            # For subscription type, only keep one entry per service
            opt_type = opt.get("type", "")
            dedup_key = f"{svc_id}_{opt_type}"
            if dedup_key in seen_services:
                continue
            seen_services.add(dedup_key)
            
            display = SERVICE_DISPLAY.get(svc_id, {})
            entry = {
                "service_id": svc_id,
                "service_name": display.get("name", svc.get("name", svc_id)),
                "service_color": display.get("color", "#ffffff"),
                "type": opt_type,
                "link": opt.get("link", ""),
                "quality": opt.get("quality", ""),
            }
            
            price = opt.get("price")
            if price:
                entry["price"] = price.get("formatted", "")
                entry["price_amount"] = price.get("amount", 0)
                entry["price_currency"] = price.get("currency", "")
            
            results.append(entry)
        
        # Sort: subscription first, then free, then rent, then buy
        type_order = {"subscription": 0, "free": 1, "addon": 2, "rent": 3, "buy": 4}
        results.sort(key=lambda x: type_order.get(x["type"], 5))
        
        return results
    except Exception as e:
        logging.error(f"Streaming API failed for movie {tmdb_id}: {e}")
        return []


async def get_cached_streaming(movie_id: int, country: str = "us") -> dict:
    """Get streaming availability with 24h MongoDB cache"""
    country = country.lower()[:2]
    
    # Check MongoDB cache
    cached = await db.streaming_cache.find_one(
        {"tmdb_id": movie_id, "country": country},
        {"_id": 0}
    )
    
    if cached:
        # Check if cache is still fresh (24 hours)
        cached_at = cached.get("cached_at", "")
        if cached_at:
            try:
                cache_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                if (datetime.now(timezone.utc) - cache_time).total_seconds() < 86400:
                    return {
                        "movie_id": movie_id,
                        "country": country,
                        "options": cached.get("options", []),
                        "cached": True
                    }
            except:
                pass
    
    # Fetch fresh data
    options = fetch_streaming_availability(movie_id, country)
    
    # Cache the result
    await db.streaming_cache.update_one(
        {"tmdb_id": movie_id, "country": country},
        {"$set": {
            "tmdb_id": movie_id,
            "country": country,
            "options": options,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {
        "movie_id": movie_id,
        "country": country,
        "options": options,
        "cached": False
    }
