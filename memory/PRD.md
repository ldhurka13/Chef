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
│   ├── .env (MONGO_URL, DB_NAME, TMDB_API_KEY, CORS_ORIGINS, JWT_SECRET, RAPIDAPI_KEY, RESEND_API_KEY)
│   ├── requirements.txt
│   ├── server.py (all endpoints, models, business logic)
│   └── tests/test_my_movies_watchlist.py
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.js (main component, routing, state management)
│       ├── index.css
│       └── components/
│           ├── AuthModal.js
│           ├── FeelingSearch.js
│           ├── FloatingNav.js (Home, Vibe, Random, My Movies, Comfort)
│           ├── LocationPermissionModal.js
│           ├── MovieCard.js
│           ├── MovieDetail.js (includes watchlist toggle button)
│           ├── MyMoviesPage.js (Diary, Watchlist, Profile tabs)
│           ├── ResetPassword.js
│           ├── UserDetails.js (Photo, Personal Info, Streaming, Letterboxd)
│           └── UserMenu.js
└── memory/
    └── PRD.md
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
- `POST /api/auth/import-letterboxd` - Letterboxd CSV import
- `GET /api/auth/letterboxd-data` - Get imported Letterboxd data
- `GET /api/user/watch-history` - Get user's diary
- `POST /api/user/watch-history` - Add to diary
- `PUT /api/user/watch-history/{tmdb_id}` - Update diary entry
- `DELETE /api/user/watch-history/{tmdb_id}` - Remove from diary
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

## DB Schema (MongoDB)
- **auth_users**: {id, email, username, password_hash, birth_year, birth_date, avatar_url, favorite_genres, favorite_actors, favorite_movies, favorite_directors, streaming_services, location_permission, location, gender, bio, letterboxd_connected, letterboxd_count, created_at}
- **watch_history**: {id, user_id, tmdb_id, user_rating, watch_dates[], last_watched_date, watch_count, title, poster_path}
- **watchlist**: {id, user_id, tmdb_id, title, poster_path, release_date, vote_average, genres[], added_at}
- **letterboxd_imports**: {user_id, entries, total_movies, rated_movies, imported_at, filename}
- **streaming_cache**: {tmdb_id, country, options, cached_at}
- **password_resets**: {user_id, email, token, expires_at, used}

## What's Been Implemented
- [x] Full dark cinematic UI with Playfair Display / Inter fonts
- [x] Hero section with trending movie
- [x] 6-section navigation (Curated, Chef's Special, Swangy, Classics, Explore, Marathon)
- [x] Floating bottom nav (Home, Vibe, Random, My Movies, Comfort)
- [x] Vibe Console with mood/energy/brain power sliders
- [x] "Hangry Hail Mary" random picks modal
- [x] "Comfort Snacks" modal with weather-aware recommendations
- [x] Semantic feeling search bar
- [x] Movie detail modal with trailer, cast, similar, streaming availability
- [x] JWT authentication (signup + login + forgot password)
- [x] Location Permission Modal
- [x] Streaming Availability ("Where to Watch") via MoviesOfTheNight API
- [x] User Details page (Photo, Gender, Bio, Streaming Services, Letterboxd)
- [x] **My Movies page with 3 tabs:**
  - [x] **Diary** - Watch history with search, add, rate (0-10 w/ 0.1 increments), date tracking, remove
  - [x] **Watchlist** - Search & add movies to watch later, remove from watchlist
  - [x] **Profile** - Favorite Genres, Favorite Actors, Favorite Directors, Top 5 Favorite Movies
- [x] Add to Watchlist button in movie detail modal (toggle on/off)
- [x] Password reset via Resend email API

## Future Tasks (P2)
- [ ] Refine Recommendation Algorithm - Rewatchability Multiplier, Complexity Penalty
- [ ] Refactor App.js into React Context providers
- [ ] Split backend/server.py into routers, models, services
