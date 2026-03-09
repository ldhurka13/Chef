# Chef - Context-Aware Movie Recommendation Engine

## Original Problem Statement
Build a context-aware movie recommendation engine called "Chef" with React frontend, FastAPI backend, and MongoDB database. Features include user authentication, recommendation algorithms, TMDB integration, local IMDB database, Letterbox'd import, and profile insights.

## Architecture

### Tech Stack
- **Frontend**: React, Tailwind CSS, Framer Motion
- **Backend**: FastAPI (Python), Motor (async MongoDB driver)
- **Database**: MongoDB (chef_db)
- **APIs**: TMDB, MoviesOfTheNight, Resend, Open-Meteo

### Key Files
- `/app/backend/server.py` - Main FastAPI application (~4400 lines)
- `/app/frontend/src/App.js` - Main React component
- `/app/frontend/src/components/MyMoviesPage.js` - Diary, Watchlist, Profile tabs
- `/app/backend/import_imdb.py` - IMDB data import script

## User Personas
1. **Casual Movie Watcher** - Uses vibe sliders, browses recommendations
2. **Film Enthusiast** - Imports Letterbox'd data, tracks detailed ratings
3. **Binge Watcher** - Uses Marathon mode, tracks rewatches

## Core Requirements (Static)
- [x] User authentication (JWT)
- [x] Movie search and discovery
- [x] Watch history with ratings
- [x] Watchlist management
- [x] Profile insights (genres, actors, directors)
- [x] Letterbox'd zip import
- [x] Local IMDB database (33K movies)

## What's Been Implemented

### Session: March 2026

#### Algorithm Enhancements
1. **Actor Impact Scoring** (March 8, 2026)
   - Role classification: Lead (order 0-2), Supporting (3-9), Background (10+)
   - Impact formula: `base_impact / role_divisor × experience × popularity`
   - Integrated into profile insights and recommendation familiarity

2. **Proportion-Based Scoring** (March 9, 2026)
   - Normalizes preferences by database availability
   - `proportion_index`: >1 means above-average preference
   - Fair comparison: Drama vs Thriller accounts for availability difference

3. **Franchise Deduplication** (March 9, 2026)
   - Groups franchise movies (MCU, Star Wars, etc.) as single entities
   - Prevents bias from actors appearing in many franchise films
   - Example: Mark Ruffalo's 9 Avengers movies count as 1 franchise entry
   - Uses TMDB `belongs_to_collection` data

#### Profile Insights Response Structure
```json
{
  "genres": [{
    "name": "Drama",
    "score": 45.2,
    "raw_score": 42.1,
    "proportion_index": 1.23,
    "franchise_count": 2,
    "standalone_count": 15
  }],
  "actors": [{
    "name": "Robert Downey Jr.",
    "score": 38.5,
    "proportion_index": 1.45,
    "avg_impact": 0.892,
    "primary_role": "lead",
    "franchise_appearances": 3,
    "standalone_appearances": 5
  }],
  "stats": {
    "total_movies_watched": 150,
    "effective_entries": 120,
    "franchises_watched": 8,
    "standalone_movies": 112
  }
}
```

## Prioritized Backlog

### P0 (Critical)
- None - Core functionality complete

### P1 (High Priority)
- [ ] Refactor server.py into modular structure (routers, models, services)
- [ ] Add "Your Lead Actors" recommendation carousel
- [ ] Display franchise breakdowns in UI

### P2 (Medium Priority)
- [ ] JustWatch API integration for streaming availability
- [ ] Refine recommendation weights based on user feedback
- [ ] Add "Because you liked X" similarity matching

### P3 (Low Priority)
- [ ] Collaborative filtering ("Users like you also watched")
- [ ] Export watch history feature
- [ ] Mobile-responsive improvements

## Key API Endpoints
- `POST /api/movies/discover` - Curated For You with vibe params
- `GET /api/user/profile-insights` - Enhanced with proportion/franchise data
- `GET /api/movies/sections/{section}` - Chef's Special, Certified Swangy, etc.
- `POST /api/auth/import-letterboxd` - Zip file import

## Database Collections
- `users` - User accounts
- `movies` - Local IMDB data (33K entries)
- `watch_history` - User diary with watches array
- `watchlist` - User's to-watch list
- `movie_metadata` - Cached TMDB data with franchise info
- `profile_insights_cache` - Computed user preferences

## Next Tasks
1. Test proportion scoring with real user data
2. Consider UI updates to show proportion_index values
3. Add franchise badges to movie cards

## Testing Status
- Backend: 100% (18 tests passed)
- Last test: iteration_16.json
