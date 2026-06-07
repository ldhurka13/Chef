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
- "My Movies" page with Diary, Watchlist, and Profile tabs

## Tech Stack
- **Frontend:** React + Tailwind CSS + Framer Motion
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Auth:** JWT tokens (custom implementation)
- **External APIs:** TMDB, MoviesOfTheNight (RapidAPI), Resend, Open-Meteo

## Architecture
```
/app/
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── server.py           # Main entry point (migrating to modular structure)
│   ├── config.py           # ✅ Settings, env vars, constants
│   ├── database.py         # ✅ MongoDB connection
│   ├── ARCHITECTURE.md     # Migration guide
│   ├── models/             # ✅ Pydantic models
│   │   ├── user.py         # User, UserRegister, UserLogin, etc.
│   │   ├── movie.py        # MovieMetadata, VibeParams, AIVibeRequest
│   │   ├── watch_history.py
│   │   ├── watchlist.py
│   │   └── game.py
│   ├── routers/            # API route handlers
│   │   └── auth.py         # ✅ Auth endpoints (9 routes)
│   ├── services/           # ✅ Business logic
│   │   ├── auth_service.py # Password hashing, JWT, get_current_user
│   │   ├── tmdb_service.py # TMDB API, caching, genres
│   │   ├── streaming.py    # MoviesOfTheNight integration
│   │   └── weather.py      # Open-Meteo weather API
│   ├── utils/              # ✅ Utilities
│   │   ├── scoring.py      # Complexity, nostalgia, rewatchability
│   │   └── helpers.py      # Vibe tags, match reasons
│   └── tests/
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.js
│       ├── index.css
│       └── components/
│           ├── AuthModal.js
│           ├── FeelingSearch.js
│           ├── FloatingNav.js
│           ├── LocationPermissionModal.js
│           ├── MovieCard.js
│           ├── MovieDetail.js
│           ├── MyMoviesPage.js
│           ├── ResetPassword.js
│           ├── UserDetails.js
│           ├── UserMenu.js
│           ├── VibeConsole.js
│           ├── SectionNav.js
│           └── MovieGame.jsx
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

## Key API Endpoints
- `POST /api/auth/register` - Sign up
- `POST /api/auth/login` - Sign in (returns token + user)
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update profile (includes favorite_directors)
- `PUT /api/auth/location-permission` - Update location preference
- `POST /api/auth/forgot-password` - Generate reset token
- `POST /api/auth/reset-password` - Reset password with token
- `POST /api/auth/upload-avatar` - Profile photo upload
- `POST /api/auth/import-letterboxd` - Letterboxd ZIP/CSV import (populates diary + watchlist)
- `GET /api/auth/letterboxd-data` - Get import status/stats
- `GET /api/user/watch-history` - Get user's diary
- `POST /api/user/watch-history` - Add to diary
- `PUT /api/user/watch-history/{tmdb_id}` - Update diary entry
- `DELETE /api/user/watch-history/{tmdb_id}` - Remove from diary
- `POST /api/user/watch-history/{tmdb_id}/watches` - Add a watch entry
- `PUT /api/user/watch-history/{tmdb_id}/watches/{watch_id}` - Edit a watch
- `DELETE /api/user/watch-history/{tmdb_id}/watches/{watch_id}` - Delete a watch
- `GET /api/user/profile-insights` - Auto-ranked top 5 genres, actors, directors from watch history
- `GET /api/user/watchlist` - Get user's watchlist
- `POST /api/user/watchlist` - Add to watchlist
- `DELETE /api/user/watchlist/{tmdb_id}` - Remove from watchlist
- `GET /api/user/watchlist/check/{tmdb_id}` - Check if in watchlist
- `GET /api/movies/search-tmdb?query=...` - TMDB movie search
- `GET /api/movies/{movie_id}/streaming` - Streaming availability
- `POST /api/movies/discover` - Curated movies by vibe params
- `GET /api/movies/trending` - Trending movies
- `GET /api/movies/sections/{section}` - Section movies
- `GET /api/movies/random-picks` - Random 3 picks
- `POST /api/movies/comfort` - Comfort movies
- `POST /api/movies/feeling-search` - Semantic search
- `GET /api/genres` - List all genres
- **Movie Game Endpoints:**
  - `POST /api/game/start` - Start 10-round King of the Hill game
  - `POST /api/game/choose` - Submit movie choice with reaction time
  - `POST /api/game/skip` - Skip round (0 points, fresh matchup)
  - `POST /api/game/cant-decide` - Equal points to both, keep King
- **AI Vibe Recommendation:**
  - `POST /api/movies/ai-vibe-recommendations` - AI-powered vibe-based recommendations with watch context

## DB Schema (MongoDB)
- **auth_users**: {id, email, username, password_hash, birth_year, birth_date, avatar_url, favorite_genres, favorite_actors, favorite_movies, favorite_directors, streaming_services, location_permission, location, gender, bio, letterboxd_connected, letterboxd_count, created_at}
- **watch_history**: {id, user_id, tmdb_id, user_rating, watch_dates[], last_watched_date, watch_count, title, poster_path, watches: [{id, rating, date, comment}]}
- **watchlist**: {id, user_id, tmdb_id, title, poster_path, release_date, vote_average, genres[], added_at}
- **letterboxd_imports**: {user_id, entries, total_movies, rated_movies, imported_at, filename}
- **streaming_cache**: {tmdb_id, country, options, cached_at}
- **password_resets**: {user_id, email, token, expires_at, used}

## What's Been Implemented
- [x] Full dark cinematic UI with Playfair Display / Inter fonts
- [x] Hero section with trending movie
- [x] 6-section navigation (Curated, Chef's Special, Swangy, Classics, Explore, Marathon)
- [x] Floating bottom nav (Home, Vibe, Random, My Movies, Game)
- [x] Vibe Console with mood/energy/brain power sliders
- [x] **AI Vibe Recommendation Engine:**
  - [x] LLM integration via Emergent Universal Key (GPT-4o)
  - [x] Hybrid web search (Reddit/Letterboxd) with LLM fallback
  - [x] Vibe sliders: Brain Power (0-100), Emotion (0-100), Energy (0-100)
  - [x] Brain Power: 0=Zoned Out (simple, background-friendly), 100=Deep Focus (complex, non-linear, dense)
  - [x] Emotion: 0=Serious (dramatic, melancholic, heavy), 100=Fun (funny, goofy, silly)
  - [x] Energy: 0=Exhausted (calming, feel-good, cozy), 100=LFG (loud, vibrant, intense)
  - [x] Vibe intersections logic (e.g., Low Brain + High Emotion = slapstick comedy)
  - [x] Watch Context selector: Solo, Date, Group
  - [x] Returns 5 hidden gem recommendations with personalized vibe_reason explanations
  - [x] Excludes watched movies when include_rewatches=false
- [x] "Hangry Hail Mary" random picks modal
- [x] **Movie Game (Eliminative Logic Discovery Engine):**
  - [x] Training Pool: ONLY movies from user's Watch History/Diary (seen films)
  - [x] Discovery Pool: Movies NOT in user's watch history (for final recommendations)
  - [x] Eliminative Logic: Maximally dissimilar pairs (different genres, eras, directors)
  - [x] King of the Hill: Winner stays on left with crown badge, loser replaced
  - [x] Reaction-Time Scoring:
    - Fast (<2s): +5 points (strong preference)
    - Average (2-5s): +2 points (standard)
    - Slow (>5s): +1 point (hesitant)
  - [x] Recency Bias: Last 3 rounds (8-10) weighted 1.3x, first 3 rounds (1-3) weighted 0.8x
  - [x] Super Like (swipe up): 2x multiplier on top of reaction score
  - [x] Skip: 0 points, keeps King if exists, fresh matchup otherwise
  - [x] Can't Decide: Equal points (+2) to both movies, King stays
  - [x] 10-round strict limit with progress bar
  - [x] Discovery Output: Top 3 movies from Discovery Pool with vector similarity matching
  - [x] "Why you'll like this" snippets (e.g., "Directed by Francis Ford Coppola, whom you love")
  - [x] Game Summary: Shows top genres, directors, and fast decision count
- [x] Semantic feeling search bar
- [x] Movie detail modal with trailer, cast, similar, streaming availability
- [x] JWT authentication (signup + login + forgot password)
- [x] Location Permission Modal
- [x] Streaming Availability ("Where to Watch") via MoviesOfTheNight API
- [x] User Details page (Photo, Gender, Bio, Streaming Services, Letterboxd)
- [x] **Curated For You - Personalized Recommendation Engine**:
  - [x] Curated score based on user's watch history (ratings, watch count, recency)
  - [x] Boosts for favorite genres, directors, and actors
  - [x] Watchlist movies prioritized (30 point boost)
  - [x] Similar movies to highly-rated content included
  - [x] Top 20 movies displayed with match percentage and reason
  - [x] Match reasons: "On your watchlist", "Your favorite genre", "Director you love", "Similar to movies you rated highly"
- [x] **My Movies page with 3 tabs:**
  - [x] **Diary** - Watch history with search, add, rate (0-10 w/ 0.1 increments), date tracking, remove
    - [x] **Diary Detail Modal** - Click any diary movie to open detailed watch history
    - [x] Multiple watches per movie (each with rating, date, comment)
    - [x] "First Watch" / "Re-watch #N" labels, descending order (latest first)
    - [x] Inline edit & delete per watch; deleting last watch removes movie from diary
    - [x] **Clear All** - Bulk delete all diary entries with confirmation modal
  - [x] **Watchlist** - Search & add movies to watch later, remove from watchlist
    - [x] **Clear All** - Bulk delete all watchlist entries with confirmation modal
  - [x] **Profile** - Top 5 Favorite Movies (user-chosen, auto-saves), auto-ranked Top Genres/Actors/Directors (read-only, computed from diary via TMDB)
    - [x] **Preference-Based Scoring** - Profile insights use "preference score" (user rating vs. Bayesian-adjusted IMDB rating)
    - [x] **Percentage Display** - Shows green ▲ x.xx% format indicating how much higher the user rates items vs. average
- [x] **Letterboxd Import**: ZIP + CSV support; ratings.csv → Diary (5→10 scale via S-curve), reviews.csv → comments, watchlist.csv → Watchlist. Orange "LB" badge on imported items
  - [x] **Non-Linear Rating Conversion** - S-curve function for nuanced Letterboxd → 10-point scale conversion
  - [x] **Familiarity-Based Adjustment** - Ratings are adjusted based on user's viewing history:
    - Calculates familiarity scores for genres, directors, and actors from existing watch history
    - Movies in genres/by directors/with actors the user has watched more get amplified ratings
    - Weights: Directors 40%, Genres 35%, Actors 25%
    - Max adjustment: ±10% of deviation from neutral (5.0)
- [x] Password reset via Resend email API

## Future Tasks (P2)
- [ ] JustWatch API Integration - Replace/augment MoviesOfTheNight for streaming availability
- [ ] Refactor App.js into React Context providers
- [x] **Split backend/server.py into modular structure** - Phase 1 Complete:
  - ✅ config.py, database.py created
  - ✅ models/ directory with all Pydantic models
  - ✅ services/ directory (auth, tmdb, streaming, weather)
  - ✅ utils/ directory (scoring, helpers)
  - ✅ routers/auth.py (9 endpoints ready)
  - 🔄 Remaining: Migrate endpoints from server.py to routers/
- [ ] Persist game sessions to MongoDB (currently in-memory - lost on server restart)

## Session Notes (April 2026)
- **Movie Game V2 Complete**: Implemented King of the Hill mechanic with reaction-time scoring, Super Like, Skip, Can't Decide features. Tested and verified 100% backend/frontend success rate.

## Session Notes (May 2026)
- **Movie Game V3 - Eliminative Logic Discovery Engine**: Major refinement implementing:
  - Data Segmentation: Training Pool (Diary only) vs Discovery Pool (unseen movies)
  - Eliminative Logic: Maximally dissimilar movie pairs for rapid mood mapping
  - Refined Scoring: Fast (<2s)=+5, Average (2-5s)=+2, Slow (>5s)=+1
  - Recency Bias: Last 3 rounds weighted 1.3x, first 3 weighted 0.8x
  - Discovery Output: Top 3 unseen movies with "Why you'll like this" snippets
- **Sort & Filter for My Movies**: Added sort (by date, rating, title, watch count) and filter (by source) to Diary and Watchlist tabs

## Session Notes (June 2026)
- **AI Vibe Recommendation Engine**: Complete implementation with:
  - GPT-4o integration via Emergent Universal Key for hidden gem recommendations
  - Corrected Emotion slider: 0=Serious (dramatic), 100=Fun (comedy)
  - Watch Context selector: Solo (introspective), Date (romantic), Group (crowd-pleaser)
  - Web search for Reddit/Letterboxd sentiment with LLM fallback
  - Personalized vibe_reason explanations for each recommendation
  - **Updated**: Now returns 20 ranked movies with vibe_score (instead of 5)
- **Vibe Console UI Refinements**:
  - Updated slider labels: Emotion (Serious/Fun), Energy (Exhausted/LFG)
  - Added margins to modal for better spacing
  - Compact rectangular watch context buttons
  - Fine-tuned vibe intersection logic (e.g., Low Brain + High Emotion = slapstick)
  - **Updated**: Reverted to bigger sliders (h-48, w-6) for better usability
- **Backend Modularization (Phase 1)**:
  - Created modular directory structure: config.py, database.py, models/, services/, utils/, routers/
  - Extracted all Pydantic models to separate files
  - Extracted services: auth_service.py, tmdb_service.py, streaming.py, weather.py
  - Extracted utilities: scoring.py, helpers.py
  - Created auth router with 9 endpoints (ready for integration)
  - Original server.py still functional (backwards compatible)
  - See /app/backend/ARCHITECTURE.md for migration guide

### Bug Fixes (Latest Session - June 7, 2026)
1. **Fixed poster display for manually added movies in Diary** - Backend now returns `poster_url` in watch history and watchlist endpoints
2. **Fixed poster display for Your Bucketlist and Discover sections** - Added `poster_url` to curated-for-you and explore-for-you endpoints
3. **Added Comment field when adding new films to Diary** - New textarea in add movie form, saved to watch entry
4. **Added Calendar View for Diary** - Interactive month-based carousel view with:
   - Toggle between List view and Calendar view
   - Movies grouped by month with navigation arrows
   - Movie cards with hover overlay showing rating and comment
   - Timeline indicator showing current position
5. **Replaced Source filter with Genre, Decade, Rating filters** - Improved filtering options in Diary tab
6. **Watchlist items now clickable** - Opens movie detail modal when clicking on watchlist items
