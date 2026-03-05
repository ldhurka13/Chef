import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
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
import SectionNav from "./components/SectionNav";
import CollectionCard from "./components/CollectionCard";
import UserMenu from "./components/UserMenu";
import AuthModal from "./components/AuthModal";
import ProfileModal from "./components/ProfileModal";
import LocationPermissionModal from "./components/LocationPermissionModal";
import UserDetails from "./components/UserDetails";
import ResetPassword from "./components/ResetPassword";
import MyMoviesPage from "./components/MyMoviesPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Page transition variants
const pageVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.5, ease: "easeInOut" } },
  exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
};

// Location helper
const requestLocationData = () => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
      },
      () => resolve(null),
      { timeout: 10000 }
    );
  });
};

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const [vibeConsoleOpen, setVibeConsoleOpen] = useState(false);
  const [movieDetailOpen, setMovieDetailOpen] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showFlash, setShowFlash] = useState(false);
  const [randomPicksOpen, setRandomPicksOpen] = useState(false);
  const [randomLoading, setRandomLoading] = useState(false);
  const [comfortOpen, setComfortOpen] = useState(false);
  const [comfortLoading, setComfortLoading] = useState(false);
  const [comfortMovies, setComfortMovies] = useState([]);
  
  // Auth state
  const [authUser, setAuthUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [locationPermissionOpen, setLocationPermissionOpen] = useState(false);
  const [pendingLoginData, setPendingLoginData] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  
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
  
  // Section state
  const [activeSection, setActiveSection] = useState("curated");
  const [sectionMovies, setSectionMovies] = useState([]);
  const [sectionLoading, setSectionLoading] = useState(false);

  // Fetch movies for a section
  const fetchSectionMovies = useCallback(async (section) => {
    setSectionLoading(true);
    try {
      let res;
      switch (section) {
        case "curated":
          res = await axios.post(`${API}/movies/discover`, vibeParams);
          break;
        case "chefs-special":
          res = await axios.get(`${API}/movies/sections/chefs-special`);
          break;
        case "certified-swangy":
          res = await axios.get(`${API}/movies/sections/certified-swangy`);
          break;
        case "all-time-classics":
          res = await axios.get(`${API}/movies/sections/all-time-classics`);
          break;
        case "explore":
          res = await axios.get(`${API}/movies/sections/explore`);
          break;
        case "marathon":
          res = await axios.get(`${API}/movies/sections/marathon`);
          break;
        default:
          res = await axios.post(`${API}/movies/discover`, vibeParams);
      }
      setSectionMovies(res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch section:", error);
      toast.error("Failed to load movies");
    } finally {
      setSectionLoading(false);
    }
  }, [vibeParams]);

  // Handle section change
  const handleSectionChange = useCallback((section) => {
    setActiveSection(section);
    fetchSectionMovies(section);
  }, [fetchSectionMovies]);

  // Auth functions
  const checkAuth = async () => {
    const token = localStorage.getItem("chef_token");
    if (token) {
      try {
        const res = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAuthUser(res.data);
        
        // Restore location permission from localStorage
        const storedPerm = localStorage.getItem("chef_location_perm");
        if (storedPerm === "always") {
          requestLocationData().then(loc => { if (loc) setUserLocation(loc); });
        }
      } catch (error) {
        localStorage.removeItem("chef_token");
      }
    }
  };

  const handleLogin = async (email, password) => {
    setAuthLoading(true);
    try {
      const res = await axios.post(`${API}/auth/login`, { email, password });
      localStorage.setItem("chef_token", res.data.token);
      setAuthUser(res.data.user);
      setAuthModalOpen(false);
      
      // Check location permission
      const storedPerm = localStorage.getItem("chef_location_perm");
      const userPerm = res.data.user.location_permission;
      
      if (userPerm === "always" || storedPerm === "always") {
        // Silently request location
        localStorage.setItem("chef_location_perm", "always");
        requestLocationData().then(loc => { if (loc) setUserLocation(loc); });
      } else if (userPerm === "never" || storedPerm === "never") {
        localStorage.setItem("chef_location_perm", "never");
      } else if (storedPerm === "ask" || userPerm === "ask") {
        // Show location modal every time
        setLocationPermissionOpen(true);
      } else {
        // No preference set yet — show modal
        setLocationPermissionOpen(true);
      }
      
      toast.success(`Welcome back, ${res.data.user.username}!`);
      return { success: true };
    } catch (error) {
      return { error: error.response?.data?.detail || "Login failed" };
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSignup = async (email, password, username, birthYear, birthDate) => {
    setAuthLoading(true);
    try {
      const res = await axios.post(`${API}/auth/register`, { 
        email, password, username, birth_year: birthYear, birth_date: birthDate || null
      });
      localStorage.setItem("chef_token", res.data.token);
      setAuthUser(res.data.user);
      setAuthModalOpen(false);
      
      // New user — always show location permission modal
      setLocationPermissionOpen(true);
      
      toast.success(`Welcome to Chef, ${res.data.user.username}!`);
      return { success: true };
    } catch (error) {
      return { error: error.response?.data?.detail || "Signup failed" };
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLocationPermission = async (option) => {
    setLocationPermissionOpen(false);
    localStorage.setItem("chef_location_perm", option);
    
    // Update backend
    const token = localStorage.getItem("chef_token");
    if (token) {
      let locationData = {};
      
      if (option === "always" || option === "ask") {
        const loc = await requestLocationData();
        if (loc) {
          setUserLocation(loc);
          locationData = { latitude: loc.latitude, longitude: loc.longitude };
        }
      }
      
      try {
        await axios.put(`${API}/auth/location-permission`, {
          location_permission: option,
          ...locationData
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (error) {
        console.error("Failed to update location permission:", error);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("chef_token");
    localStorage.removeItem("chef_location_perm");
    setAuthUser(null);
    setUserLocation(null);
    toast.success("Logged out successfully");
  };

  const handleUpdateProfile = async (data) => {
    const token = localStorage.getItem("chef_token");
    try {
      const res = await axios.put(`${API}/auth/profile`, data, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAuthUser(res.data);
      toast.success("Profile updated!");
    } catch (error) {
      toast.error("Failed to update profile");
    }
  };

  // Initialize data
  useEffect(() => {
    // Check auth on mount
    checkAuth();
    
    const initializeData = async () => {
      try {
        // Seed initial data (mock user for default sections)
        await axios.post(`${API}/seed-data`).catch(() => {});
        
        // Fetch trending movies for hero
        const trendingRes = await axios.get(`${API}/movies/trending`);
        setTrendingMovies(trendingRes.data.results || []);
        
        // Fetch watch history (requires auth)
        const token = localStorage.getItem("chef_token");
        if (token) {
          const historyRes = await axios.get(`${API}/user/watch-history`, {
            headers: { Authorization: `Bearer ${token}` }
          }).catch(() => ({ data: [] }));
          setWatchHistory(historyRes.data || []);
        }
        
        // Initial section load (curated)
        await fetchSectionMovies("curated");
      } catch (error) {
        console.error("Failed to initialize:", error);
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
  const handleVibeChange = useCallback(async (newParams) => {
    setVibeParams(newParams);
    // If on curated section, refresh it
    if (activeSection === "curated") {
      setSectionLoading(true);
      try {
        const res = await axios.post(`${API}/movies/discover`, newParams);
        setSectionMovies(res.data.results || []);
      } catch (error) {
        console.error("Failed to update curated:", error);
      } finally {
        setSectionLoading(false);
      }
    }
  }, [activeSection]);

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
      const hour = new Date().getHours();
      
      // Build request with location if available
      const comfortPayload = { hour };
      if (userLocation) {
        comfortPayload.latitude = userLocation.latitude;
        comfortPayload.longitude = userLocation.longitude;
      }
      
      const res = await axios.post(`${API}/movies/comfort`, comfortPayload);
      
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
      const token = localStorage.getItem("chef_token");
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      await axios.post(`${API}/user/watch-history`, {
        tmdb_id: movie.id,
        user_rating: rating,
        title: movie.title,
        poster_path: movie.poster_path,
      }, { headers });
      
      // Refresh watch history
      const historyRes = await axios.get(`${API}/user/watch-history`, { headers });
      setWatchHistory(historyRes.data || []);
      
      toast.success("Added to your watch history");
    } catch (error) {
      console.error("Failed to add to history:", error);
      toast.error("Failed to add to watch history");
    }
  };

  const heroMovie = trendingMovies[0];

  return (
    <div className="min-h-screen bg-chef-bg text-chef-platinum relative">
      <FilmGrain />
      <ShutterFlash show={showFlash} />
      
      {/* Top Bar - Logo, Search, User Menu */}
      <div className="fixed top-0 left-0 right-0 z-30 px-4 md:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          {/* Logo */}
          <a href="/" className="flex-shrink-0" data-testid="chef-logo">
            <img src="/logo.png" alt="Chef" className="h-[72px] w-[72px] object-contain -rotate-12" />
          </a>
          
          {/* Feeling Search - centered */}
          <div className="flex-1 flex justify-center">
            <div className="w-full max-w-xl">
              <FeelingSearch onMovieClick={handleMovieClick} />
            </div>
          </div>
          
          {/* User Menu */}
          <div className="flex-shrink-0">
            <UserMenu
              user={authUser}
              onLogout={handleLogout}
              onProfileClick={() => setProfileModalOpen(true)}
              onDetailsClick={() => navigate("/details")}
              onSettingsClick={() => setProfileModalOpen(true)}
              onLoginClick={() => {
                setAuthMode("login");
                setAuthModalOpen(true);
              }}
              onSignupClick={() => {
                setAuthMode("signup");
                setAuthModalOpen(true);
              }}
            />
          </div>
        </div>
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
                <main className="pb-24 pt-16">
                  {/* Hero Section */}
                  <HeroSection 
                    movie={heroMovie} 
                    loading={loading}
                    onMovieClick={handleMovieClick}
                  />
                  
                  {/* Section Navigation & Movies */}
                  <section className="px-4 md:px-8 max-w-7xl mx-auto mt-4">
                    <SectionNav 
                      activeSection={activeSection}
                      onSectionChange={handleSectionChange}
                    />
                    
                    {activeSection === "marathon" ? (
                      /* Marathon Collection Grid */
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {sectionLoading || loading ? (
                          [...Array(6)].map((_, index) => (
                            <div key={index} className="h-[420px] rounded-lg skeleton" />
                          ))
                        ) : (
                          sectionMovies.map((collection, index) => (
                            <motion.div
                              key={collection.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.05, duration: 0.4 }}
                            >
                              <CollectionCard
                                collection={collection}
                                onClick={() => {
                                  // For collections, we could open a special modal
                                  // For now, open first movie in the collection
                                  if (collection.parts && collection.parts.length > 0) {
                                    handleMovieClick({ id: collection.parts[0].id });
                                  }
                                }}
                                index={index}
                              />
                            </motion.div>
                          ))
                        )}
                      </div>
                    ) : (
                      <MovieGrid 
                        movies={sectionMovies}
                        loading={sectionLoading || loading}
                        onMovieClick={handleMovieClick}
                      />
                    )}
                  </section>
                </main>
              }
            />
            <Route
              path="/my-movies"
              element={
                <MyMoviesPage user={authUser} onUserUpdate={(updated) => setAuthUser(updated)} />
              }
            />
            <Route
              path="/details"
              element={
                <UserDetails
                  user={authUser}
                  onUserUpdate={(updated) => setAuthUser(updated)}
                />
              }
            />
            <Route
              path="/reset-password"
              element={<ResetPassword />}
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
            <h2 className="font-serif text-2xl md:text-3xl text-center mb-2 text-chef-platinum">
              The Hangry Hail Mary
            </h2>
            <p className="text-center text-chef-muted/60 text-sm mb-8">
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
                    className="bg-chef-surface/30 border border-white/5 overflow-hidden"
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
                    className="bg-chef-surface/50 backdrop-blur-sm border border-white/5 overflow-hidden cursor-pointer group"
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
                        <div className="w-full h-full bg-chef-surface flex items-center justify-center">
                          <span className="text-chef-muted">No Image</span>
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      {movie.match_percentage && (
                        <div className="absolute top-3 right-3 px-2 py-1 bg-chef-teal/20 border border-chef-teal/30 text-chef-teal text-xs">
                          {movie.match_percentage}%
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3 className="font-serif text-lg truncate">{movie.title}</h3>
                      <p className="text-sm text-chef-teal mt-1">{movie.vibe_tag}</p>
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
                className="flex items-center gap-2 text-chef-teal hover:text-chef-platinum transition-colors text-sm disabled:opacity-50"
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
                className="text-chef-muted hover:text-chef-platinum transition-colors text-sm"
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
            <h2 className="font-serif text-2xl md:text-3xl text-center mb-2 text-chef-gold">
              Your Comfort Snacks
            </h2>
            <p className="text-center text-chef-muted/60 text-sm mb-8">
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
                    className="bg-chef-surface/30 border border-chef-gold/10 overflow-hidden"
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
                    className="bg-chef-surface/50 backdrop-blur-sm border border-chef-gold/20 overflow-hidden cursor-pointer group"
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
                        <div className="w-full h-full bg-chef-surface flex items-center justify-center">
                          <span className="text-chef-muted">No Image</span>
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                      {movie.user_rating && (
                        <div className="absolute top-3 right-3 px-2 py-1 bg-chef-gold/20 border border-chef-gold/30 text-chef-gold text-xs">
                          {movie.user_rating}/10
                        </div>
                      )}
                      {movie.watch_count > 1 && (
                        <div className="absolute top-3 left-3 px-2 py-1 bg-chef-surface/80 text-chef-muted text-xs">
                          Watched {movie.watch_count}x
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3 className="font-serif text-lg truncate">{movie.title}</h3>
                      <p className="text-sm text-chef-gold mt-1">{movie.vibe_tag}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-chef-muted">No comfort movies yet.</p>
                <p className="text-chef-muted/60 text-sm mt-2">
                  Rate some movies 7+ to build your comfort collection!
                </p>
              </div>
            )}
            
            {/* Close Button */}
            <div className="mt-8 flex items-center justify-center">
              <button
                onClick={() => setComfortOpen(false)}
                className="text-chef-muted hover:text-chef-platinum transition-colors text-sm"
                data-testid="close-comfort-btn"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}
      
      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        mode={authMode}
        onModeChange={setAuthMode}
        onLogin={handleLogin}
        onSignup={handleSignup}
        loading={authLoading}
      />
      
      {/* Location Permission Modal */}
      <LocationPermissionModal
        isOpen={locationPermissionOpen}
        onSelect={handleLocationPermission}
      />
      
      {/* Profile Modal */}
      <ProfileModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        user={authUser}
        watchHistory={watchHistory}
        onUpdateProfile={handleUpdateProfile}
      />
      
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
