"""
Weather service - Open-Meteo API integration for comfort movie recommendations.
"""
import time
import logging
import requests

# Weather cache (short TTL since weather changes)
weather_cache = {}
WEATHER_CACHE_TTL = 1800  # 30 minutes


def fetch_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather from Open-Meteo API (free, no key needed)"""
    cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"
    cached = weather_cache.get(cache_key)
    if cached and time.time() - cached["ts"] < WEATHER_CACHE_TTL:
        return cached["data"]
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "hourly": "temperature_2m,relative_humidity_2m,rain,weathercode",
            "forecast_days": 1,
            "timezone": "auto"
        }
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        current = data.get("current_weather", {})
        temperature = current.get("temperature", 20)
        weathercode = current.get("weathercode", 0)
        
        # WMO Weather codes: 0-3 clear/cloudy, 45-48 fog, 51-67 drizzle/rain, 71-77 snow, 80-99 showers/thunderstorms
        is_rainy = weathercode in range(51, 100) or weathercode in [45, 48]
        is_cold = temperature < 12
        is_snowy = weathercode in range(71, 78)
        is_hot = temperature > 30
        
        weather_data = {
            "temperature": temperature,
            "weathercode": weathercode,
            "is_cold": is_cold,
            "is_rainy": is_rainy,
            "is_snowy": is_snowy,
            "is_hot": is_hot,
            "description": get_weather_description(weathercode, temperature)
        }
        
        weather_cache[cache_key] = {"data": weather_data, "ts": time.time()}
        return weather_data
    except Exception as e:
        logging.error(f"Weather API failed: {e}")
        return {"temperature": 20, "weathercode": 0, "is_cold": False, "is_rainy": False, "is_snowy": False, "is_hot": False, "description": ""}


def get_weather_description(weathercode: int, temperature: float) -> str:
    """Convert WMO weather code to human description"""
    if weathercode <= 3:
        base = "clear skies" if weathercode <= 1 else "partly cloudy"
    elif weathercode <= 48:
        base = "foggy"
    elif weathercode <= 57:
        base = "light drizzle"
    elif weathercode <= 67:
        base = "rainy"
    elif weathercode <= 77:
        base = "snowy"
    elif weathercode <= 82:
        base = "rain showers"
    else:
        base = "stormy"
    
    if temperature < 0:
        return f"Freezing & {base}"
    elif temperature < 12:
        return f"Chilly & {base}"
    elif temperature > 30:
        return f"Hot & {base}"
    return base.capitalize()


def generate_comfort_vibe_tag(watch_count: int, user_rating: int, hour: int, is_cold: bool, is_rainy: bool, is_snowy: bool, weather_description: str) -> str:
    """Generate context-aware vibe tag for comfort movies"""
    if watch_count >= 3:
        return "Your go-to comfort classic"
    if is_snowy:
        return "Perfect for a snowy day indoors"
    if is_rainy:
        return "Ideal for a rainy day"
    if is_cold:
        return "Warm up with this favorite"
    if user_rating >= 9:
        return "A certified favorite"
    if hour >= 22 or hour < 6:
        return "Perfect for late night unwinding"
    if hour >= 18:
        return "Evening comfort pick"
    return "Comfort food for your soul"
