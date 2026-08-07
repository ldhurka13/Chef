/**
 * StarterLibraryOnboarding.js
 * 
 * A modal component for collecting initial movie taste data from new users.
 * Shows after successful registration and re-prompts if user has < 5 diary entries.
 * Uses TMDB Popular movies with infinite scroll for better variety.
 */
import { useState, useEffect, useRef, useCallback, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { 
  X, Upload, Film, Star, Loader2, 
  Sparkles, ArrowRight, RefreshCw, AlertCircle, Plus, Check
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;
const MINIMUM_MOVIES = 5;
const MOVIES_PER_PAGE = 15;

// Helper to get auth headers
const authHeaders = () => {
  const token = localStorage.getItem("chef_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Movie card for quick-add selection - memoized to prevent unnecessary re-renders
const QuickAddMovieCard = memo(({ movie, onAdd, isAdding, onFadeComplete }) => {
  const [showRating, setShowRating] = useState(false);
  const [rating, setRating] = useState(7.0);
  const [isExiting, setIsExiting] = useState(false);
  
  const handleAdd = async () => {
    setIsExiting(true);
    await onAdd(movie, rating);
    // Callback to parent to remove this card
    setTimeout(() => {
      if (onFadeComplete) onFadeComplete(movie.id);
    }, 300);
  };
  
  const releaseYear = movie.release_date ? movie.release_date.substring(0, 4) : "";
  const posterUrl = movie.poster_url || (movie.poster_path ? `https://image.tmdb.org/t/p/w185${movie.poster_path}` : null);
  
  // Exiting state - fade out animation
  if (isExiting) {
    return (
      <div 
        className="relative aspect-[2/3] rounded-xl overflow-hidden animate-fade-out"
        data-testid={`onboarding-movie-exiting-${movie.id}`}
        style={{ animation: 'fadeOut 0.3s ease-out forwards' }}
      >
        {posterUrl && (
          <img src={posterUrl} alt={movie.title} className="w-full h-full object-cover" />
        )}
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>
    );
  }
  
  // Rating popup - clean minimal design with grey tones
  if (showRating) {
    return (
      <div
        className="relative aspect-[2/3] rounded-xl overflow-hidden bg-chef-surface border border-white/20 shadow-xl"
        data-testid={`onboarding-movie-rating-${movie.id}`}
      >
        {/* Background poster blur */}
        {posterUrl && (
          <div className="absolute inset-0">
            <img src={posterUrl} alt="" className="w-full h-full object-cover opacity-15 blur-sm" />
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
              <Star className="w-5 h-5 text-chef-platinum" fill="currentColor" />
              <span className="text-2xl font-serif text-chef-platinum">{rating.toFixed(1)}</span>
            </div>
            
            {/* Slider - grey/neutral styling */}
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={rating}
              onChange={(e) => setRating(parseFloat(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.5) ${rating * 10}%, rgba(255,255,255,0.1) ${rating * 10}%, rgba(255,255,255,0.1) 100%)`
              }}
              aria-label="Rating slider"
            />
            <div className="flex justify-between mt-1 text-[9px] text-chef-muted">
              <span>0</span>
              <span>10</span>
            </div>
          </div>
          
          {/* Add button - sleek minimal "+" design */}
          <button
            onClick={handleAdd}
            disabled={isAdding}
            className="w-full py-2.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-chef-platinum disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center"
            data-testid={`onboarding-add-btn-${movie.id}`}
          >
            {isAdding ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Plus className="w-5 h-5" strokeWidth={2} />
            )}
          </button>
        </div>
      </div>
    );
  }
  
  // Default state - clickable card (no motion animations to prevent flickering)
  return (
    <div 
      className="relative group cursor-pointer transition-transform duration-150 hover:scale-[1.02] active:scale-[0.98]"
      data-testid={`onboarding-movie-${movie.id}`}
    >
      <div 
        className="aspect-[2/3] rounded-xl overflow-hidden bg-chef-surface/40 border border-white/10 group-hover:border-white/30 transition-all duration-200"
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
            <div className="mt-2 flex items-center gap-1.5 text-white/70">
              <Plus className="w-3 h-3" />
              <span className="text-[10px] font-medium">Click to rate</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

QuickAddMovieCard.displayName = 'QuickAddMovieCard';

// Progress indicator component
const ProgressIndicator = ({ current, total }) => {
  const percentage = Math.min((current / total) * 100, 100);
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-white/40 to-white/60 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
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
  const [visibleMovies, setVisibleMovies] = useState([]);
  const [loadingMovies, setLoadingMovies] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [movieError, setMovieError] = useState(false);
  const [addedCount, setAddedCount] = useState(0);
  const [addingMovieId, setAddingMovieId] = useState(null);
  const [isSkipping, setIsSkipping] = useState(false);
  const [existingDiaryCount, setExistingDiaryCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  
  // Letterboxd import state
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(null);
  const fileInputRef = useRef(null);
  
  const modalRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const loadMoreTriggerRef = useRef(null);
  
  // Use refs for values that shouldn't trigger re-renders when used in callbacks
  const existingIdsRef = useRef(new Set());
  const isFetchingRef = useRef(false);
  const isInitializedRef = useRef(false);
  const currentPageRef = useRef(1);
  
  // Total movies added (existing + new)
  const totalMoviesAdded = existingDiaryCount + addedCount;
  
  // Fetch movies - stable callback that reads from refs
  const fetchMovies = useCallback(async (page = 1) => {
    // Prevent duplicate fetches
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    
    if (page === 1) {
      setLoadingMovies(true);
      setMovieError(false);
    } else {
      setLoadingMore(true);
    }
    
    try {
      const res = await axios.get(`${API}/api/onboarding/popular-movies`, {
        params: { page, per_page: MOVIES_PER_PAGE },
        headers: authHeaders()
      });
      
      const fetchedMovies = res.data?.results || [];
      const hasMoreMovies = res.data?.has_more ?? false;
      
      // Filter out user's existing movies using ref
      const existingIds = existingIdsRef.current;
      const filteredMovies = fetchedMovies.filter(m => !existingIds.has(m.id));
      
      if (page === 1) {
        setVisibleMovies(filteredMovies);
      } else {
        setVisibleMovies(prev => {
          const existingVisibleIds = new Set(prev.map(m => m.id));
          const newMovies = filteredMovies.filter(m => !existingVisibleIds.has(m.id));
          return [...prev, ...newMovies];
        });
      }
      
      setCurrentPage(page);
      currentPageRef.current = page;
      setHasMore(hasMoreMovies);
    } catch (err) {
      console.error("Failed to fetch movies:", err);
      if (page === 1) {
        setMovieError(true);
      }
    } finally {
      setLoadingMovies(false);
      setLoadingMore(false);
      isFetchingRef.current = false;
    }
  }, []); // No dependencies - uses refs
  
  // Initialize data when modal opens - only runs once per open
  useEffect(() => {
    if (!isOpen) {
      // Reset initialization flag when modal closes
      isInitializedRef.current = false;
      return;
    }
    
    // Prevent double initialization
    if (isInitializedRef.current) return;
    isInitializedRef.current = true;
    
    const initializeData = async () => {
      // Reset state
      setAddedCount(0);
      setVisibleMovies([]);
      setCurrentPage(1);
      currentPageRef.current = 1;
      isFetchingRef.current = false;
      
      try {
        // Fetch user's existing movies for exclusion
        const [diaryRes, watchlistRes, eligibilityRes] = await Promise.all([
          axios.get(`${API}/api/user/watch-history`, { headers: authHeaders() }).catch(() => ({ data: [] })),
          axios.get(`${API}/api/user/watchlist`, { headers: authHeaders() }).catch(() => ({ data: [] })),
          axios.get(`${API}/api/onboarding/eligibility`, { headers: authHeaders() }).catch(() => ({ data: { diary_count: 0 } }))
        ]);
        
        setExistingDiaryCount(eligibilityRes.data?.diary_count || 0);
        
        // Store existing IDs in ref (not state) to avoid re-renders
        existingIdsRef.current = new Set([
          ...(diaryRes.data || []).map(m => m.tmdb_id),
          ...(watchlistRes.data || []).map(m => m.tmdb_id)
        ]);
        
        // Now fetch movies
        await fetchMovies(1);
      } catch (err) {
        console.error("Failed to initialize:", err);
        setMovieError(true);
        setLoadingMovies(false);
      }
    };
    
    initializeData();
  }, [isOpen, fetchMovies]);
  
  // Infinite scroll using Intersection Observer
  useEffect(() => {
    const trigger = loadMoreTriggerRef.current;
    const container = scrollContainerRef.current;
    
    if (!trigger || !container || !hasMore || loadingMore || loadingMovies) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isFetchingRef.current) {
          fetchMovies(currentPageRef.current + 1);
        }
      },
      { 
        root: container,
        rootMargin: '200px',
        threshold: 0.1 
      }
    );
    
    observer.observe(trigger);
    
    return () => {
      observer.disconnect();
    };
  }, [hasMore, loadingMore, loadingMovies, fetchMovies]);
  
  // Handle movie card fade complete
  const handleMovieFadeComplete = useCallback((movieId) => {
    setVisibleMovies(prev => prev.filter(m => m.id !== movieId));
  }, []);
  
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
  const handleAddMovie = useCallback(async (movie, rating) => {
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
      
      // Update added count
      setAddedCount(prev => prev + 1);
      
      // Add to existing IDs ref so it doesn't show up in future pages
      existingIdsRef.current.add(movie.id);
      
      const newTotal = existingDiaryCount + addedCount + 1;
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
  }, [addingMovieId, existingDiaryCount, addedCount, onRefreshLibrary]);
  
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
        
        try {
          await axios.post(`${API}/api/onboarding/complete`, {}, { headers: authHeaders() });
        } catch (e) {
          // Non-critical
        }
        
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
    if (addedCount > 0 && onComplete) {
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
                  <Sparkles className="w-5 h-5 text-chef-platinum" />
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
          
          {/* Content - Scrollable */}
          <div 
            ref={scrollContainerRef}
            className="px-6 py-5 overflow-y-auto max-h-[calc(85vh-180px)]"
          >
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
                <Film className="w-4 h-4 text-chef-muted" />
                Popular movies you might have seen
              </h3>
              
              {loadingMovies ? (
                // Loading skeleton
                <div className="grid grid-cols-4 sm:grid-cols-5 gap-3">
                  {[...Array(MOVIES_PER_PAGE)].map((_, i) => (
                    <div key={`skeleton-${i}`} className="aspect-[2/3] rounded-xl bg-chef-surface/40 animate-pulse" />
                  ))}
                </div>
              ) : movieError ? (
                // Error state
                <div className="text-center py-8">
                  <AlertCircle className="w-8 h-8 text-red-400/60 mx-auto mb-2" />
                  <p className="text-sm text-chef-muted mb-3">Failed to load movies</p>
                  <button
                    onClick={() => {
                      isInitializedRef.current = false;
                      setMovieError(false);
                    }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-chef-surface/60 text-chef-platinum text-sm hover:bg-white/10 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Try again
                  </button>
                </div>
              ) : visibleMovies.length === 0 ? (
                // No movies available
                <div className="text-center py-8">
                  <Film className="w-8 h-8 text-chef-muted/30 mx-auto mb-2" />
                  <p className="text-sm text-chef-muted">No new movies to show</p>
                  <p className="text-xs text-chef-muted/60">Try the Letterboxd import above</p>
                </div>
              ) : (
                <>
                  {/* Movie grid */}
                  <div className="grid grid-cols-4 sm:grid-cols-5 gap-3">
                    {visibleMovies.map((movie) => (
                      <QuickAddMovieCard
                        key={movie.id}
                        movie={movie}
                        onAdd={handleAddMovie}
                        isAdding={addingMovieId === movie.id}
                        onFadeComplete={handleMovieFadeComplete}
                      />
                    ))}
                  </div>
                  
                  {/* Load more trigger / Loading indicator */}
                  <div 
                    ref={loadMoreTriggerRef} 
                    className="mt-6 flex justify-center"
                  >
                    {loadingMore ? (
                      <div className="flex items-center gap-2 text-chef-muted text-sm py-4">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Loading more movies...</span>
                      </div>
                    ) : hasMore ? (
                      <div className="text-chef-muted/50 text-xs py-4">
                        Scroll for more movies
                      </div>
                    ) : visibleMovies.length > 0 ? (
                      <div className="text-chef-muted/50 text-xs py-4">
                        You&apos;ve seen all available movies
                      </div>
                    ) : null}
                  </div>
                </>
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
                {addedCount > 0 && (
                  <span className="text-xs text-chef-muted">
                    +{addedCount} movie{addedCount !== 1 ? "s" : ""} added
                  </span>
                )}
                <button
                  onClick={handleDone}
                  className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                    hasReachedMinimum 
                      ? "bg-white/20 border border-white/30 text-chef-platinum hover:bg-white/30" 
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
