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
import EmergencyButton from "./components/EmergencyButton";
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
  const [safetyNetOpen, setSafetyNetOpen] = useState(false);
  
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
  const [emergencyMovies, setEmergencyMovies] = useState([]);
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

  // Handle emergency button
  const handleEmergency = async () => {
    setShowFlash(true);
    
    // Play shutter sound (optional - browser may block autoplay)
    try {
      const audio = new Audio("data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleRMMStXg7J9tIw5H09rnnXMrElHX3ue8hj0TSdLZ56R6NBdT1drmv4s6E0rR2OehdjIYUtTZ5cCNOxNL0djno3g0GFPVz+K9izkTStHY56R6NBhT1c/ivYs5E0rR2OekezUYU9XP4r2LORNK0djnpHs1GFPV0OK+izoTStHY56R7NRhT1dDivYs5E0rR2OekejQYU9XQ4r6LORNKz9fnpXs1GFLV0OK9ijkTSs/X56R6NBhT1dDivYo5E0rP1+ejejQYUtXQ4ryJOBNKz9bno3o0GFLU0OK8iTgTSs/W5qN6NBhS1NDiu4g4E0rP1uajejQYUtTQ4ruIOBNKz9bmo3o0GFLU0OK7iDgTSs/W5qN6NBhS1NDiu4g4E0rPz+WiejMYU9TP4rqHNxNKz9XnonkzGFHUzuG6hjcTS8/V5qJ5MxhR1M7guoY3E0vP1eaieTMYUdTO4LqGNxNLz9Xmonk");
      audio.volume = 0.3;
      audio.play().catch(() => {});
    } catch {}
    
    setTimeout(() => setShowFlash(false), 300);
    
    try {
      const res = await axios.get(`${API}/movies/emergency`);
      setEmergencyMovies(res.data.results || []);
      setSafetyNetOpen(true);
    } catch (error) {
      console.error("Failed to get emergency movies:", error);
      toast.error("No comfort movies found - add some favorites first!");
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
        onEmergencyClick={handleEmergency}
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
      
      {/* Safety Net (Emergency Results) */}
      {safetyNetOpen && emergencyMovies.length > 0 && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setSafetyNetOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="max-w-4xl w-full sepia-tone"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-serif text-3xl md:text-4xl text-center mb-8 text-flick-gold">
              Your Comfort Classics
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {emergencyMovies.map((movie, index) => (
                <motion.div
                  key={movie.tmdb_id || index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-2xl overflow-hidden cursor-pointer group"
                  onClick={() => {
                    setSafetyNetOpen(false);
                    handleMovieClick({ id: movie.tmdb_id, ...movie });
                  }}
                  data-testid={`emergency-movie-${index}`}
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
                  </div>
                  <div className="p-4">
                    <h3 className="font-serif text-lg truncate">{movie.title}</h3>
                    <p className="text-sm text-flick-gold mt-1">{movie.vibe_tag}</p>
                    <p className="text-sm text-flick-muted mt-1">
                      Your rating: {movie.user_rating}/10
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
            <button
              onClick={() => setSafetyNetOpen(false)}
              className="mt-8 mx-auto block text-flick-muted hover:text-flick-platinum transition-colors"
              data-testid="close-emergency-btn"
            >
              Close
            </button>
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
