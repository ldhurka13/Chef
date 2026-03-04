import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";

// Components
import HeroSection from "./components/HeroSection";
import MovieGrid from "./components/MovieGrid";
import FloatingNav from "./components/FloatingNav";
import VibeConsole from "./components/VibeConsole";
import MovieDetail from "./components/MovieDetail";
import SafetyNet from "./components/SafetyNet";
import FilmGrain from "./components/FilmGrain";
import ShutterFlash from "./components/ShutterFlash";
import FeelingSearch from "./components/FeelingSearch";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Page transition variants
const pageVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.5, ease: "easeInOut" } },
  exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
};

function AppContent() {
  const location = useLocation();
  const [vibeConsoleOpen, setVibeConsoleOpen] = useState(false);
  const [movieDetailOpen, setMovieDetailOpen] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showFlash, setShowFlash] = useState(false);
  const [randomPicksOpen, setRandomPicksOpen] = useState(false);
  const [randomLoading, setRandomLoading] = useState(false);
  const [comfortOpen, setComfortOpen] = useState(false);
  const [comfortLoading, setComfortLoading] = useState(false);
  const [comfortMovies, setComfortMovies] = useState([]);
  
  // Vibe parameters
  const [vibeParams, setVibeParams] = useState({
    brain_power: 50,
    mood: 50,
    energy: 50,
    include_rewatches: false,
  });
  
  // Data states
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [discoveredMovies, setDiscoveredMovies] = useState([]);
  const [randomMovies, setRandomMovies] = useState([]);
  const [watchHistory, setWatchHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [discoverLoading, setDiscoverLoading] = useState(false);

  // Initialize data
  useEffect(() => {
    const initializeData = async () => {
      try {
        // Seed initial data
        await axios.post(`${API}/seed-data`);
        
        // Fetch trending movies
        const trendingRes = await axios.get(`${API}/movies/trending`);
        setTrendingMovies(trendingRes.data.results || []);
        
        // Fetch watch history
        const historyRes = await axios.get(`${API}/user/watch-history`);
        setWatchHistory(historyRes.data || []);
        
        // Initial discover
        await discoverMovies(vibeParams);
      } catch (error) {
        console.error("Failed to initialize:", error);
        toast.error("Failed to load movies");
      } finally {
        setLoading(false);
      }
    };
    
    initializeData();
  }, []);

  // Discover movies based on vibe params
  const discoverMovies = useCallback(async (params) => {
    setDiscoverLoading(true);
    try {
      const res = await axios.post(`${API}/movies/discover`, params);
      setDiscoveredMovies(res.data.results || []);
    } catch (error) {
      console.error("Failed to discover movies:", error);
      toast.error("Failed to discover movies");
    } finally {
      setDiscoverLoading(false);
    }
  }, []);

  // Handle vibe change
  const handleVibeChange = useCallback((newParams) => {
    setVibeParams(newParams);
    discoverMovies(newParams);
  }, [discoverMovies]);

  // Handle random movie picks
  const handleRandomPicks = async (isRefresh = false) => {
    if (!isRefresh) {
      setRandomPicksOpen(true);
    }
    setRandomLoading(true);
    setRandomMovies([]);
    
    try {
      const res = await axios.get(`${API}/movies/random-picks`);
      // Small delay to ensure smooth transition
      await new Promise(resolve => setTimeout(resolve, 300));
      setRandomMovies(res.data.results || []);
    } catch (error) {
      console.error("Failed to get random picks:", error);
      toast.error("Failed to get movie recommendations");
      if (!isRefresh) {
        setRandomPicksOpen(false);
      }
    } finally {
      setRandomLoading(false);
    }
  };

  // Handle comfort movies
  const handleComfort = async () => {
    setComfortOpen(true);
    setComfortLoading(true);
    
    try {
      // Get current hour for time-based recommendations
      const hour = new Date().getHours();
      
      const res = await axios.post(`${API}/movies/comfort`, {
        hour: hour,
        is_cold: false,  // Could be enhanced with weather API
        is_rainy: false
      });
      
      await new Promise(resolve => setTimeout(resolve, 300));
      setComfortMovies(res.data.results || []);
    } catch (error) {
      console.error("Failed to get comfort movies:", error);
      toast.error("Add some favorites to your history first!");
      setComfortOpen(false);
    } finally {
      setComfortLoading(false);
    }
  };

  // Handle movie click
  const handleMovieClick = (movie) => {
    setSelectedMovie(movie);
    setMovieDetailOpen(true);
  };

  // Handle add to watch history
  const handleAddToHistory = async (movie, rating) => {
    try {
      await axios.post(`${API}/user/watch-history`, {
        tmdb_id: movie.id,
        user_rating: rating,
        title: movie.title,
        poster_path: movie.poster_path,
      });
      
      // Refresh watch history
      const historyRes = await axios.get(`${API}/user/watch-history`);
      setWatchHistory(historyRes.data || []);
      
      toast.success("Added to your watch history");
    } catch (error) {
      console.error("Failed to add to history:", error);
      toast.error("Failed to add to watch history");
    }
  };

  const heroMovie = trendingMovies[0];

  return (
    <div className="min-h-screen bg-flick-bg text-flick-platinum relative">
      <FilmGrain />
      <ShutterFlash show={showFlash} />
      
      {/* Feeling Search - Fixed at Top */}
      <div className="fixed top-6 left-0 right-0 z-30">
        <FeelingSearch onMovieClick={handleMovieClick} />
      </div>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <Routes>
            <Route
              path="/"
              element={
                <main className="pb-24">
                  {/* Hero Section */}
                  <HeroSection 
                    movie={heroMovie} 
                    loading={loading}
                    onMovieClick={handleMovieClick}
                  />
                  
                  {/* Movie Discovery Grid */}
                  <section className="px-4 md:px-8 max-w-7xl mx-auto mt-12">
                    <h2 className="font-serif text-2xl md:text-3xl tracking-tight mb-8">
                      Curated for You
                    </h2>
                    
                    <MovieGrid 
                      movies={discoveredMovies}
                      loading={discoverLoading || loading}
                      onMovieClick={handleMovieClick}
                    />
                  </section>
                  
                  {/* Trending Section */}
                  <section className="px-4 md:px-8 max-w-7xl mx-auto mt-20">
                    <h2 className="font-serif text-2xl md:text-3xl tracking-tight mb-8">
                      Trending This Week
                    </h2>
                    <MovieGrid 
                      movies={trendingMovies.slice(1)}
                      loading={loading}
                      onMovieClick={handleMovieClick}
                    />
                  </section>
                </main>
              }
            />
            <Route
              path="/history"
              element={
                <main className="pb-24 pt-8">
                  <section className="px-4 md:px-8 max-w-7xl mx-auto">
                    <h1 className="font-serif text-3xl md:text-4xl tracking-tight mb-8">
                      Your Watch History
                    </h1>
                    <SafetyNet 
                      movies={watchHistory}
                      onMovieClick={handleMovieClick}
                    />
                  </section>
                </main>
              }
            />
          </Routes>
        </motion.div>
      </AnimatePresence>
      
      {/* Floating Navigation */}
      <FloatingNav 
        onVibeClick={() => setVibeConsoleOpen(true)}
        onRandomClick={() => handleRandomPicks(false)}
        onComfortClick={handleComfort}
      />
      
      {/* Vibe Console Modal */}
      <VibeConsole 
        open={vibeConsoleOpen}
        onOpenChange={setVibeConsoleOpen}
        params={vibeParams}
        onParamsChange={handleVibeChange}
      />
      
      {/* Movie Detail Modal */}
      <MovieDetail 
        open={movieDetailOpen}
        onOpenChange={setMovieDetailOpen}
        movie={selectedMovie}
        onAddToHistory={handleAddToHistory}
      />
      
      {/* Random Picks Modal */}
      {randomPicksOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
          onClick={() => setRandomPicksOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-4xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-serif text-2xl md:text-3xl text-center mb-2 text-flick-platinum">
              The Hangry Hail Mary
            </h2>
            <p className="text-center text-flick-muted/60 text-sm mb-8">
              For when you don't care what it is, as long as it's hot
            </p>
            
            {/* Loading State */}
            {randomLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[0, 1, 2].map((index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-flick-surface/30 border border-white/5 overflow-hidden"
                  >
                    <div className="aspect-[2/3] skeleton" />
                    <div className="p-4 space-y-2">
                      <div className="h-5 w-3/4 skeleton rounded" />
                      <div className="h-4 w-1/2 skeleton rounded" />
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {randomMovies.map((movie, index) => (
                  <motion.div
                    key={movie.id || index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.15, duration: 0.4 }}
                    className="bg-flick-surface/50 backdrop-blur-sm border border-white/5 overflow-hidden cursor-pointer group"
                    onClick={() => {
                      setRandomPicksOpen(false);
                      handleMovieClick(movie);
                    }}
                    data-testid={`random-movie-${index}`}
                  >
                    <div className="aspect-[2/3] relative overflow-hidden">
                      {movie.poster_url ? (
                        <img
                          src={movie.poster_url}
                          alt={movie.title}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                      ) : (
                        <div className="w-full h-full bg-flick-surface flex items-center justify-center">
                          <span className="text-flick-muted">No Image</span>
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      {movie.match_percentage && (
                        <div className="absolute top-3 right-3 px-2 py-1 bg-flick-teal/20 border border-flick-teal/30 text-flick-teal text-xs">
                          {movie.match_percentage}%
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3 className="font-serif text-lg truncate">{movie.title}</h3>
                      <p className="text-sm text-flick-teal mt-1">{movie.vibe_tag}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="mt-8 flex items-center justify-center gap-6">
              <button
                onClick={() => handleRandomPicks(true)}
                disabled={randomLoading}
                className="flex items-center gap-2 text-flick-teal hover:text-flick-platinum transition-colors text-sm disabled:opacity-50"
                data-testid="refresh-random-btn"
              >
                <svg 
                  className={`w-4 h-4 ${randomLoading ? 'animate-spin' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
              <button
                onClick={() => setRandomPicksOpen(false)}
                className="text-flick-muted hover:text-flick-platinum transition-colors text-sm"
                data-testid="close-random-btn"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Comfort Movies Modal */}
      {comfortOpen && (
        <div 
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
          onClick={() => setComfortOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-4xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-serif text-2xl md:text-3xl text-center mb-2 text-flick-gold">
              Your Comfort Snacks
            </h2>
            <p className="text-center text-flick-muted/60 text-sm mb-8">
              Familiar favorites for when you need a warm hug
            </p>
            
            {/* Loading State */}
            {comfortLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[0, 1, 2].map((index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-flick-surface/30 border border-flick-gold/10 overflow-hidden"
                  >
                    <div className="aspect-[2/3] skeleton" />
                    <div className="p-4 space-y-2">
                      <div className="h-5 w-3/4 skeleton rounded" />
                      <div className="h-4 w-1/2 skeleton rounded" />
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : comfortMovies.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {comfortMovies.map((movie, index) => (
                  <motion.div
                    key={movie.id || movie.tmdb_id || index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.15, duration: 0.4 }}
                    className="bg-flick-surface/50 backdrop-blur-sm border border-flick-gold/20 overflow-hidden cursor-pointer group"
                    onClick={() => {
                      setComfortOpen(false);
                      handleMovieClick(movie);
                    }}
                    data-testid={`comfort-movie-${index}`}
                  >
                    <div className="aspect-[2/3] relative overflow-hidden">
                      {movie.poster_url ? (
                        <img
                          src={movie.poster_url}
                          alt={movie.title}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                        />
                      ) : (
                        <div className="w-full h-full bg-flick-surface flex items-center justify-center">
                          <span className="text-flick-muted">No Image</span>
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      {movie.user_rating && (
                        <div className="absolute top-3 right-3 px-2 py-1 bg-flick-gold/20 border border-flick-gold/30 text-flick-gold text-xs">
                          {movie.user_rating}/10
                        </div>
                      )}
                      {movie.watch_count > 1 && (
                        <div className="absolute top-3 left-3 px-2 py-1 bg-flick-surface/80 text-flick-muted text-xs">
                          Watched {movie.watch_count}x
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3 className="font-serif text-lg truncate">{movie.title}</h3>
                      <p className="text-sm text-flick-gold mt-1">{movie.vibe_tag}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-flick-muted">No comfort movies yet.</p>
                <p className="text-flick-muted/60 text-sm mt-2">
                  Rate some movies 7+ to build your comfort collection!
                </p>
              </div>
            )}
            
            {/* Close Button */}
            <div className="mt-8 flex items-center justify-center">
              <button
                onClick={() => setComfortOpen(false)}
                className="text-flick-muted hover:text-flick-platinum transition-colors text-sm"
                data-testid="close-comfort-btn"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}
      
      <Toaster 
        position="bottom-center"
        toastOptions={{
          style: {
            background: '#161618',
            color: '#E5E5E5',
            border: '1px solid rgba(255,255,255,0.1)',
          },
        }}
      />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
