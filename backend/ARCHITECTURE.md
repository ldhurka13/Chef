# Chef Backend - Modular Architecture

## Directory Structure

```
/app/backend/
├── server.py              # Main entry point (5400+ lines - needs incremental migration)
├── server_backup.py       # Backup of original monolith
├── config.py              # ✅ Settings, env vars, constants
├── database.py            # ✅ MongoDB connection
│
├── models/                # ✅ Pydantic models (fully migrated)
│   ├── __init__.py        # Re-exports all models
│   ├── user.py            # User, UserRegister, UserLogin, UserProfile, UserUpdate
│   ├── movie.py           # MovieMetadata, VibeParams, AIVibeRequest, ComfortRequest
│   ├── watch_history.py   # WatchHistoryItem, WatchEntryCreate, etc.
│   ├── watchlist.py       # WatchlistAdd
│   └── game.py            # GameChoiceV2
│
├── routers/               # API route handlers
│   ├── __init__.py
│   └── auth.py            # ✅ /auth/* endpoints (ready to integrate)
│   # TODO: user.py        # /user/* endpoints (watch-history, watchlist, profile-insights)
│   # TODO: movies.py      # /movies/* endpoints
│   # TODO: game.py        # /game/* endpoints
│
├── services/              # ✅ Business logic (fully migrated)
│   ├── __init__.py        # Re-exports all services
│   ├── auth_service.py    # Password hashing, JWT tokens, get_current_user
│   ├── tmdb_service.py    # TMDB API requests, caching, image URLs, genres
│   ├── streaming.py       # MoviesOfTheNight streaming availability
│   └── weather.py         # Open-Meteo weather for comfort movies
│
└── utils/                 # ✅ Utilities (fully migrated)
    ├── __init__.py        # Re-exports all utilities
    ├── scoring.py         # Complexity, nostalgia, rewatchability calculations
    └── helpers.py         # Vibe tags, match reasons, feeling search
```

## Migration Status

### ✅ Completed
- **config.py** - All configuration and environment variables
- **database.py** - MongoDB connection management
- **models/** - All Pydantic models extracted
- **services/** - Core services (auth, tmdb, streaming, weather)
- **utils/** - Scoring algorithms and helper functions
- **routers/auth.py** - Authentication routes (9 endpoints)

### 🔄 In Progress
- Main server.py still contains all endpoint implementations
- Routes can be incrementally moved to routers/

### 📋 TODO
- Create `routers/user.py` for watch-history, watchlist, profile-insights
- Create `routers/movies.py` for discover, trending, sections, streaming
- Create `routers/game.py` for movie game endpoints
- Update server.py to import from routers instead of inline definitions

## How to Continue Migration

### Step 1: Add Router Import to server.py
```python
from routers.auth import router as auth_router
api_router.include_router(auth_router)
```

### Step 2: Remove Duplicate Endpoints
After including the router, remove the corresponding inline endpoint definitions.

### Step 3: Repeat for Each Router
1. Create new router file (e.g., `routers/user.py`)
2. Move endpoint functions from server.py
3. Import and include the router
4. Test thoroughly

## Import Examples

```python
# Models
from models import User, UserRegister, VibeParams, AIVibeRequest

# Services
from services.auth_service import hash_password, get_current_user
from services.tmdb_service import tmdb_request, get_image_url, get_genre_map

# Utils
from utils.scoring import calculate_flick_score
from utils.helpers import generate_vibe_tag, get_match_reason
```

## Testing After Migration

```bash
# Test imports
cd /app/backend && python3 -c "from models import *; from services import *; from utils import *; print('OK')"

# Test API
curl https://diary-watch.preview.emergentagent.com/api/
curl -X POST https://diary-watch.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```
