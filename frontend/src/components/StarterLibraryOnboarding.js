/**
 * StarterLibraryOnboarding.js
 * 
 * A modal component for collecting initial movie taste data from new users.
 * Shows after successful registration and re-prompts if user has < 5 diary entries.
 * Uses TMDB Popular movies for better variety.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { 
  X, Upload, Film, Star, Loader2, Check, 
  Sparkles, ArrowRight, RefreshCw, AlertCircle, Plus
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;
const MINIMUM_MOVIES = 5;

// Helper to get auth headers
const authHeaders = () => {
  const token = localStorage.getItem("chef_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Movie card for quick-add selection - Cleaner expanded card design
const QuickAddMovieCard = ({ movie, onAdd, isAdding, isAdded }) => {
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(7.0);
  
  const handleAdd = async () => {
    await onAdd(movie, rating);
    setShowRating(false);
  };
  
  const releaseYear = movie.release_date ? movie.release_date.substring(0, 4) : "";
  const posterUrl = movie.poster_url || (movie.poster_path ? `https://image.tmdb.org/t/p/w185${movie.poster_path}` : null);
  
  // Added state - compact checkmark overlay
  if (isAdded) {
    return (
      <motion.div 
        initial={{ scale: 0.95 }}
        animate={{ scale: 1 }}
        className="relative aspect-[2/3] rounded-xl overflow-hidden bg-gradient-to-br from-chef-teal/20 to-chef-teal/5 border border-chef-teal/40"
        data-testid={`onboarding-movie-added-${movie.id}`}
      >
        {posterUrl && (
          <img src={posterUrl} alt={movie.title} className="w-full h-full object-cover opacity-30" />
        )}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", damping: 15 }}
            className="flex flex-col items-center gap-1"
          >
            <div className="w-10 h-10 rounded-full bg-chef-teal/30 flex items-center justify-center">
              <Check className="w-5 h-5 text-chef-teal" />
            </div>
            <span className="text-[10px] text-chef-teal font-medium mt-1">Added</span>
          </motion.div>
        </div>
      </motion.div>
    );
  }
  
  // Rating popup expanded - cleaner design
  if (showRating) {
    return (
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="relative aspect-[2/3] rounded-xl overflow-hidden bg-chef-surface border border-chef-teal/30 shadow-lg shadow-chef-teal/10"
        data-testid={`onboarding-movie-rating-${movie.id}`}
      >
        {/* Background poster blur */}
        {posterUrl && (
          <div className="absolute inset-0">
            <img src={posterUrl} alt="" className="w-full h-full object-cover opacity-20 blur-sm" />
          </div>
        )}
        
        {/* Content overlay */}
        <div className="relative z-10 h-full flex flex-col p-3">
          {/* Header with close */}
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-chef-platinum font-medium line-clamp-2">{movie.title}</p>
              {releaseYear && <p className="text-[10px] text-chef-muted">{releaseYear}</p>}
            </div>
            <button
              onClick={() => setShowRating(false)}
              className="p-1 -mr-1 -mt-1 text-chef-muted hover:text-chef-platinum rounded-full hover:bg-white/5 transition-colors"
              aria-label="Cancel"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          
          {/* Rating display */}
          <div className="flex-1 flex flex-col justify-center">
            <div className="flex items-center justify-center gap-1.5 mb-3">
              <Star className="w-5 h-5 text-chef-gold" fill="currentColor" />
              <span className="text-2xl font-serif text-chef-gold">{rating.toFixed(1)}</span>
            </div>
            
            {/* Slider */}
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={rating}
              onChange={(e) => setRating(parseFloat(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none bg-white/10 accent-chef-gold cursor-pointer"
              style={{
                background: `linear-gradient(to right, #d4af37 0%, #d4af37 ${rating * 10}%, rgba(255,255,255,0.1) ${rating * 10}%, rgba(255,255,255,0.1) 100%)`
              }}
              aria-label="Rating slider"
            />
            <div className="flex justify-between mt-1 text-[9px] text-chef-muted">
              <span>0</span>
              <span>10</span>
            </div>
          </div>
          
          {/* Add button */}
          <button
            onClick={handleAdd}
            disabled={isAdding}
            className="w-full py-2.5 rounded-lg bg-chef-teal/20 border border-chef-teal/40 text-chef-teal text-xs font-medium hover:bg-chef-teal/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
            data-testid={`onboarding-add-btn-${movie.id}`}
          >
            {isAdding ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <Plus className="w-3.5 h-3.5" />
                Add to Diary
              </>
            )}
          </button>
        </div>
      </motion.div>
    );
  }
  
  // Default state - clickable card
  return (
    <motion.div 
      className="relative group cursor-pointer"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      data-testid={`onboarding-movie-${movie.id}`}
    >
      <div 
        className="aspect-[2/3] rounded-xl overflow-hidden bg-chef-surface/40 border border-white/10 group-hover:border-chef-teal/40 transition-all duration-200"
        onClick={() => !isAdding && setShowRating(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && !isAdding && setShowRating(true)}
        aria-label={`Add ${movie.title} to diary`}
      >
        {posterUrl ? (
          <img src={posterUrl} alt={movie.title} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-chef-surface/60">
            <Film className="w-8 h-8 text-chef-muted/30" />
          </div>
        )}
        
        {/* Hover overlay with movie info */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="absolute bottom-0 left-0 right-0 p-3">
            <p className="text-xs text-chef-platinum font-medium line-clamp-2">{movie.title}</p>
            {releaseYear && <p className="text-[10px] text-chef-muted mt-0.5">{releaseYear}</p>}
            
            {/* Quick add hint */}
            <div className="mt-2 flex items-center gap-1.5 text-chef-teal">
              <Plus className="w-3 h-3" />
              <span className="text-[10px] font-medium">Click to rate & add</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// Progress indicator component
const ProgressIndicator = ({ current, total }) => {
  const percentage = Math.min((current / total) * 100, 100);
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <motion.div 
          className="h-full bg-gradient-to-r from-chef-teal to-chef-gold rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-chef-muted whitespace-nowrap">
        {current} / {total} movies
      </span>
    </div>
  );
};

// Main onboarding modal
const StarterLibraryOnboarding = ({
  isOpen,
  onClose,
  onComplete,
  user,
  onRefreshLibrary
}) => {
  const [movies, setMovies] = useState([]);
  const [loadingMovies, setLoadingMovies] = useState(true);
  const [movieError, setMovieError] = useState(false);
  const [addedMovies, setAddedMovies] = useState(new Set());
  const [addingMovieId, setAddingMovieId] = useState(null);
  const [isSkipping, setIsSkipping] = useState(false);
  const [existingDiaryCount, setExistingDiaryCount] = useState(0);
  
  // Letterboxd import state
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(null);
  const fileInputRef = useRef(null);
  
  const modalRef = useRef(null);
  
  // Total movies added (existing + new)
  const totalMoviesAdded = existingDiaryCount + addedMovies.size;
  const moviesNeeded = Math.max(0, MINIMUM_MOVIES - totalMoviesAdded);
  
  // Fetch popular movies on mount
  const fetchMovies = useCallback(async () => {
    setLoadingMovies(true);
    setMovieError(false);
    
    try {
      // Get popular movies from onboarding endpoint
      const res = await axios.get(`${API}/api/onboarding/popular-movies`, {
        headers: authHeaders()
      });
      
      const allMovies = res.data?.results || [];
      
      // Get user's existing diary and watchlist to exclude
      const [diaryRes, watchlistRes, eligibilityRes] = await Promise.all([
        axios.get(`${API}/api/user/watch-history`, { headers: authHeaders() }).catch(() => ({ data: [] })),
        axios.get(`${API}/api/user/watchlist`, { headers: authHeaders() }).catch(() => ({ data: [] })),
        axios.get(`${API}/api/onboarding/eligibility`, { headers: authHeaders() }).catch(() => ({ data: { diary_count: 0 } }))
      ]);
      
      // Set existing diary count for progress tracking
      setExistingDiaryCount(eligibilityRes.data?.diary_count || 0);
      
      const existingIds = new Set([
        ...(diaryRes.data || []).map(m => m.tmdb_id),
        ...(watchlistRes.data || []).map(m => m.tmdb_id)
      ]);
      
      // Filter out existing movies
      const filteredMovies = allMovies.filter(m => !existingIds.has(m.id));
      
      setMovies(filteredMovies);
    } catch (err) {
      console.error("Failed to fetch movies:", err);
      setMovieError(true);
    } finally {
      setLoadingMovies(false);
    }
  }, []);
  
  useEffect(() => {
    if (isOpen) {
      fetchMovies();
    }
  }, [isOpen, fetchMovies]);
  
  // Handle escape key
  const handleSkip = useCallback(async () => {
    setIsSkipping(true);
    
    try {
      await axios.post(`${API}/api/onboarding/skip`, { skipped: true }, { headers: authHeaders() });
    } catch (err) {
      console.error("Failed to persist skip:", err);
    } finally {
      setIsSkipping(false);
      onClose();
    }
  }, [onClose]);
  
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        handleSkip();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, handleSkip]);
  
  // Handle adding a movie to diary
  const handleAddMovie = async (movie, rating) => {
    if (addingMovieId) return;
    
    setAddingMovieId(movie.id);
    
    try {
      const posterPath = movie.poster_path || 
        (movie.poster_url ? movie.poster_url.replace("https://image.tmdb.org/t/p/w185", "").replace("https://image.tmdb.org/t/p/w500", "") : null);
      
      await axios.post(`${API}/api/user/watch-history`, {
        tmdb_id: movie.id,
        user_rating: rating,
        watched_date: new Date().toISOString().split("T")[0],
        title: movie.title,
        poster_path: posterPath,
        comment: ""
      }, { headers: authHeaders() });
      
      // Mark as added
      setAddedMovies(prev => new Set([...prev, movie.id]));
      
      const newTotal = existingDiaryCount + addedMovies.size + 1;
      const remaining = Math.max(0, MINIMUM_MOVIES - newTotal);
      
      if (remaining > 0) {
        toast.success(`Added "${movie.title}"! ${remaining} more to go.`);
      } else {
        toast.success(`Added "${movie.title}"! You've unlocked full features!`);
      }
      
      // Mark onboarding as completed
      try {
        await axios.post(`${API}/api/onboarding/complete`, {}, { headers: authHeaders() });
      } catch (e) {
        // Non-critical
      }
      
      // Refresh library data
      if (onRefreshLibrary) {
        onRefreshLibrary();
      }
    } catch (err) {
      console.error("Failed to add movie:", err);
      toast.error(err.response?.data?.detail || "Failed to add movie. Please try again.");
    } finally {
      setAddingMovieId(null);
    }
  };
  
  // Handle Letterboxd file import
  const handleLetterboxdImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.name.endsWith('.zip')) {
      toast.error("Please upload a ZIP file from Letterboxd export");
      return;
    }
    
    setIsImporting(true);
    setImportProgress("Uploading...");
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      setImportProgress("Processing your Letterboxd data...");
      
      const res = await axios.post(`${API}/api/auth/import-letterboxd`, formData, {
        headers: {
          ...authHeaders(),
          "Content-Type": "multipart/form-data"
        }
      });
      
      const { imported, watchlist_added } = res.data;
      
      if (imported > 0 || watchlist_added > 0) {
        toast.success(`Imported ${imported} diary entries and ${watchlist_added} watchlist items!`);
        
        // Mark onboarding as completed
        try {
          await axios.post(`${API}/api/onboarding/complete`, {}, { headers: authHeaders() });
        } catch (e) {
          // Non-critical
        }
        
        // Refresh library and close
        if (onRefreshLibrary) {
          onRefreshLibrary();
        }
        
        if (onComplete) {
          onComplete();
        }
        onClose();
      } else {
        toast.error("No movies could be imported. Please check your export file.");
      }
    } catch (err) {
      console.error("Letterboxd import failed:", err);
      toast.error(err.response?.data?.detail || "Import failed. Please try again.");
    } finally {
      setIsImporting(false);
      setImportProgress(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };
  
  // Handle done
  const handleDone = () => {
    if (addedMovies.size > 0 && onComplete) {
      onComplete();
    }
    onClose();
  };
  
  if (!isOpen) return null;
  
  const hasReachedMinimum = totalMoviesAdded >= MINIMUM_MOVIES;
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        onClick={handleSkip}
        data-testid="onboarding-modal-backdrop"
      >
        <motion.div
          ref={modalRef}
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative w-full max-w-3xl max-h-[85vh] overflow-hidden bg-chef-bg border border-white/10 rounded-2xl shadow-cinematic"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="onboarding-title"
        >
          {/* Header */}
          <div className="sticky top-0 z-10 bg-chef-bg/95 backdrop-blur-sm border-b border-white/5 px-6 py-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles className="w-5 h-5 text-chef-gold" />
                  <h2 id="onboarding-title" className="font-serif text-xl text-chef-platinum">
                    Build your movie taste profile
                  </h2>
                </div>
                <p className="text-sm text-chef-muted">
                  Add at least {MINIMUM_MOVIES} films to unlock personalized recommendations
                </p>
              </div>
              <button
                onClick={handleSkip}
                className="p-2 rounded-lg text-chef-muted hover:text-chef-platinum hover:bg-white/5 transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Progress bar */}
            <ProgressIndicator current={totalMoviesAdded} total={MINIMUM_MOVIES} />
          </div>
          
          {/* Content */}
          <div className="px-6 py-5 overflow-y-auto max-h-[calc(85vh-180px)]">
            {/* Letterboxd Import Section */}
            <div className="mb-6 p-4 rounded-xl bg-chef-surface/40 border border-white/5">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-orange-500/10">
                  <Upload className="w-5 h-5 text-orange-400" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-chef-platinum mb-1">
                    Import from Letterboxd
                  </h3>
                  <p className="text-xs text-chef-muted mb-3">
                    Already track films on Letterboxd? Import your diary and watchlist instantly.
                  </p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".zip"
                    onChange={handleLetterboxdImport}
                    className="hidden"
                    id="letterboxd-file"
                    disabled={isImporting}
                  />
                  
                  <label
                    htmlFor="letterboxd-file"
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors
                      ${isImporting 
                        ? "bg-orange-500/10 text-orange-400/50 cursor-not-allowed" 
                        : "bg-orange-500/10 border border-orange-500/20 text-orange-400 hover:bg-orange-500/20"}`}
                  >
                    {isImporting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        {importProgress || "Importing..."}
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Upload Letterboxd ZIP
                      </>
                    )}
                  </label>
                </div>
              </div>
            </div>
            
            {/* Divider */}
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-xs text-chef-muted uppercase tracking-wider">or quick-add</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>
            
            {/* Quick Add Movies Section */}
            <div>
              <h3 className="text-sm font-medium text-chef-platinum mb-4 flex items-center gap-2">
                <Film className="w-4 h-4 text-chef-teal" />
                Popular movies you might have seen
              </h3>
              
              {loadingMovies ? (
                // Loading skeleton
                <div className="grid grid-cols-4 sm:grid-cols-5 gap-3">
                  {[...Array(15)].map((_, i) => (
                    <div key={i} className="aspect-[2/3] rounded-xl bg-chef-surface/40 animate-pulse" />
                  ))}
                </div>
              ) : movieError ? (
                // Error state
                <div className="text-center py-8">
                  <AlertCircle className="w-8 h-8 text-red-400/60 mx-auto mb-2" />
                  <p className="text-sm text-chef-muted mb-3">Failed to load movies</p>
                  <button
                    onClick={fetchMovies}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-chef-surface/60 text-chef-platinum text-sm hover:bg-white/10 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Try again
                  </button>
                </div>
              ) : movies.length === 0 ? (
                // No movies available
                <div className="text-center py-8">
                  <Film className="w-8 h-8 text-chef-muted/30 mx-auto mb-2" />
                  <p className="text-sm text-chef-muted">No new movies to show</p>
                  <p className="text-xs text-chef-muted/60">Try the Letterboxd import above</p>
                </div>
              ) : (
                // Movie grid - larger cards with 5 columns
                <div className="grid grid-cols-4 sm:grid-cols-5 gap-3">
                  {movies.map((movie) => (
                    <QuickAddMovieCard
                      key={movie.id}
                      movie={movie}
                      onAdd={handleAddMovie}
                      isAdding={addingMovieId === movie.id}
                      isAdded={addedMovies.has(movie.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Footer */}
          <div className="sticky bottom-0 bg-chef-bg/95 backdrop-blur-sm border-t border-white/5 px-6 py-4">
            <div className="flex items-center justify-between">
              <button
                onClick={handleSkip}
                disabled={isSkipping}
                className="px-4 py-2 rounded-lg text-sm text-chef-muted hover:text-chef-platinum transition-colors disabled:opacity-50"
                data-testid="onboarding-skip-btn"
              >
                {isSkipping ? "Skipping..." : "Skip for now"}
              </button>
              
              <div className="flex items-center gap-3">
                {addedMovies.size > 0 && (
                  <span className="text-xs text-chef-teal">
                    +{addedMovies.size} movie{addedMovies.size !== 1 ? "s" : ""} added
                  </span>
                )}
                <button
                  onClick={handleDone}
                  className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                    hasReachedMinimum 
                      ? "bg-chef-teal/30 border border-chef-teal/50 text-chef-teal hover:bg-chef-teal/40" 
                      : "bg-chef-surface border border-white/10 text-chef-platinum hover:bg-white/10"
                  }`}
                  data-testid="onboarding-done-btn"
                >
                  {hasReachedMinimum ? (
                    <>
                      <Check className="w-4 h-4" />
                      Done
                    </>
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default StarterLibraryOnboarding;
