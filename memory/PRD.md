# Chef - Context-Aware Movie Recommendation Engine

## Original Problem Statement
Build a context-aware movie recommendation engine called "Chef" with:
- A premium, cinematic dark-themed UI
- Vibe Console with mood sliders for personalized recommendations
- Multiple discovery sections (Curated, Chef's Special, Certified Swangy, All Time Classics, Explore, Marathon)
- Semantic feeling search bar
- "Hangry Hail Mary" random picks
- "Comfort Snacks" for familiar favorites
- Full user authentication with birth date and location
- TMDB integration for movie data

## Tech Stack
- **Frontend:** React + Tailwind CSS + Framer Motion
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Auth:** JWT tokens (custom implementation)
- **External API:** TMDB

## Architecture
```
/app/
├── backend/
│   ├── .env (MONGO_URL, DB_NAME, TMDB_API_KEY, CORS_ORIGINS)
│   ├── requirements.txt
│   ├── server.py (all endpoints, models, business logic)
│   └── tests/test_auth.py
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.js (main component, state management)
│       ├── index.css
│       └── components/ (AuthModal, LocationPermissionModal, FloatingNav, etc.)
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `POST /api/auth/register` - Sign up (email, password, username, birth_year, birth_date)
- `POST /api/auth/login` - Sign in (returns token + user with location_permission)
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update profile
- `PUT /api/auth/location-permission` - Update location preference (always/ask/never)
- `GET /api/movies/{movie_id}/streaming?country=us` — Streaming availability (Movies of the Night API, 24hr MongoDB cache)
- `GET /api/user/watch-history` — Get authenticated user's watch history (sorted by most recent)
- `POST /api/user/watch-history` — Add movie to history (rating 0-10 float, watch date, tracks multiple watches)
- `PUT /api/user/watch-history/{tmdb_id}` — Update rating or add watch date
- `DELETE /api/user/watch-history/{tmdb_id}` — Remove movie from history
- `GET /api/movies/search-tmdb?query=...` — TMDB movie search (for favorite movie picker)
- `POST /api/auth/upload-avatar` — Profile photo upload (JPEG/PNG/WebP, max 2MB)
- `POST /api/auth/import-letterboxd` — Letterboxd CSV import
- `GET /api/auth/letterboxd-data` — Get imported Letterboxd data
- `POST /api/movies/discover` - Curated movies by vibe params
- `GET /api/movies/trending` - Trending movies
- `GET /api/movies/sections/{section}` - Section movies (chefs-special, certified-swangy, all-time-classics, explore, marathon)
- `GET /api/movies/random-picks` - Random 3 picks
- `POST /api/movies/comfort` - Comfort movies
- `POST /api/movies/feeling-search` - Semantic search
- `GET /api/movies/{movie_id}` - Movie details

## DB Schema (MongoDB)
- **auth_users**: {id, email, username, password_hash, birth_year, birth_date, avatar_url, favorite_genres, location_permission, location, gender, bio, favorite_actors, favorite_movies, letterboxd_connected, letterboxd_count, created_at}
- **letterboxd_imports**: {user_id, entries, total_movies, rated_movies, imported_at, filename}
- **users**: {id, username, birth_year, created_at} (mock user for demo)
- **watch_history**: {id, user_id, tmdb_id, user_rating, last_watched_date, watch_count, title, poster_path}

- **streaming_cache**: {tmdb_id, country, options, cached_at} (24hr TTL)

## What's Been Implemented
- [x] Full dark cinematic UI with Playfair Display / Inter fonts
- [x] Hero section with trending movie
- [x] 6-section navigation (Curated, Chef's Special, Swangy, Classics, Explore, Marathon)
- [x] Floating bottom nav (Home, Vibe, Random, History, Comfort)
- [x] Vibe Console with mood/energy/brain power sliders
- [x] "Hangry Hail Mary" random picks modal
- [x] "Comfort Snacks" modal
- [x] Semantic feeling search bar
- [x] Movie detail modal with trailer, cast, similar
- [x] Watch history tracking
- [x] JWT authentication (signup + login)
- [x] Birth Date field on signup (full date, not just year)
- [x] App renamed from "Flick" to "Chef"
- [x] Location Permission Modal (Always / Ask Every Time / Never)
- [x] Location permission stored in localStorage + backend
- [x] Token key renamed from flick_token to chef_token
- [x] Comfort feature uses real weather data (Open-Meteo API)
- [x] Streaming Availability — "Where to Watch" in movie detail modal (Movies of the Night API, MongoDB cached, 7 services)
- [x] User Details page (/details) — Gender, Bio, Profile Photo upload, Favorite Actors, Top 5 Favorite Movies (TMDB search), Connect Letterboxd (CSV import)
- [x] Streaming Services selection — 7-service checkbox grid (Netflix, Prime, Disney+, Hulu, Apple TV+, Max, Paramount+) persisted to user profile
- [x] Watch History CRUD — Add movies via TMDB search, rate 0-10 with 0.1 increments, track multiple watch dates per movie, remove movies, all per-authenticated user

## Upcoming Tasks (P1)
- [x] Integrate Location/Time into "Comfort" Logic - uses Open-Meteo weather API with real lat/lng, time-of-day scoring, weather-aware vibe tags

## Future Tasks (P2)
- [ ] JustWatch API Integration - "Where to Watch" on movie cards
- [ ] Refine Recommendation Algorithm - Rewatchability Multiplier, Complexity Penalty
- [ ] Refactor App.js into React Context providers
- [ ] Split backend/server.py into routers, models, services
