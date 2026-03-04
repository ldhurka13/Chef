# Flick - Context-Aware Movie Recommendation Engine
## Product Requirements Document

### Original Problem Statement
Build "Flick," a context-aware movie recommendation engine using TMDB API with:
- Vibe Console with sliders for Brain Power, Mood, Energy
- "I Can't Even" Emergency Button for instant rewatch recommendations
- Movie discovery with Match % and Vibe Tags
- Flick Scoring Algorithm with Rewatchability, Nostalgia Bonus, Complexity Penalty
- Premium cinematic dark theme

### Architecture
- **Frontend**: React + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + MongoDB
- **External API**: TMDB API for movie data
- **Database**: MongoDB (users, watch_history collections)

### User Personas
1. **Casual Viewer**: Tired after work, wants easy comfort viewing
2. **Film Enthusiast**: Looking for quality cinema with depth
3. **Social Watcher**: Needs crowd-pleaser recommendations

### Core Requirements (Static)
- [x] TMDB API integration for movie discovery
- [x] Flick Scoring Algorithm implementation
- [x] Vibe Console with 3 parameters
- [x] Emergency Rewatch feature
- [x] Watch History management
- [x] Dark cinematic UI theme

### What's Been Implemented (March 2026)

#### Backend (server.py)
- [x] MongoDB models: Users, WatchHistory
- [x] TMDB API service with caching
- [x] Flick Scoring Algorithm:
  - Base Score from TMDB rating
  - Rewatchability Multiplier (days since watched, user rating)
  - Nostalgia Bonus (+2.0 for birth_year+12 to +22 releases)
  - Complexity Penalty (energy-based genre filtering)
- [x] **Feeling Search (Chat Feature)**:
  - Natural language mood parsing
  - FEELING_MAPPINGS for 40+ emotions/vibes
  - Semantic search with genre/keyword matching
- [x] API Endpoints:
  - GET /api/movies/trending
  - POST /api/movies/discover (with vibe params)
  - POST /api/movies/feeling-search (NEW - Chat feature)
  - GET /api/movies/emergency
  - GET /api/movies/{id}
  - GET /api/user/profile
  - GET/POST/DELETE /api/user/watch-history
  - POST /api/seed-data

#### Frontend Components
- [x] **FeelingSearch** - Transparent search bar at top with suggestions
- [x] HeroSection - "Vibe of the Day" featured movie
- [x] VibeConsole - Modal with vertical sliders
- [x] EmergencyButton - "I Can't Even" with shutter flash
- [x] MovieGrid - Masonry layout for movie cards
- [x] MovieCard - Poster with Match % and Vibe Tags
- [x] MovieDetail - Full details modal with trailer
- [x] FloatingNav - Bottom navigation bar
- [x] SafetyNet - Sepia-toned watch history
- [x] FilmGrain - Subtle texture overlay
- [x] ShutterFlash - Camera flash animation

### Prioritized Backlog

#### P0 (Done)
- [x] Core recommendation engine
- [x] TMDB integration
- [x] Vibe Console
- [x] Emergency rewatch feature

#### P1 (Next)
- [ ] JustWatch API integration for "Where to Watch"
- [ ] User authentication (optional)
- [ ] Pagination for movie discovery
- [ ] Search functionality

#### P2 (Future)
- [ ] TV Show support
- [ ] Social sharing features
- [ ] Watchlist functionality
- [ ] Push notifications for trending movies

### Next Tasks
1. Integrate JustWatch/RapidAPI for streaming availability
2. Add pagination to discover endpoint
3. Implement movie search
4. Add user preferences persistence
