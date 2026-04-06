import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform } from "framer-motion";
import { X, SkipForward, Sparkles, Trophy, RotateCcw, ChevronUp } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TMDB_IMG = "https://image.tmdb.org/t/p/";

const getToken = () => localStorage.getItem("chef_token");
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

// Swipeable Movie Card Component
const SwipeableCard = ({ movie, onSelect, onSuperLike, side, isActive }) => {
  const cardRef = useRef(null);
  const y = useMotionValue(0);
  const opacity = useTransform(y, [-100, 0], [0.5, 1]);
  const scale = useTransform(y, [-100, 0], [1.05, 1]);
  
  const [isDragging, setIsDragging] = useState(false);
  const [showSuperLike, setShowSuperLike] = useState(false);

  const handleDragEnd = (event, info) => {
    setIsDragging(false);
    // Swipe up threshold for super-like
    if (info.offset.y < -80) {
      setShowSuperLike(true);
      setTimeout(() => {
        onSuperLike(movie);
      }, 300);
    }
  };

  if (!movie) return null;

  return (
    <motion.div
      ref={cardRef}
      className={`relative flex-1 max-w-[45%] aspect-[2/3] rounded-2xl overflow-hidden cursor-pointer
                  border-2 transition-colors duration-300
                  ${isActive ? 'border-chef-teal/50' : 'border-white/10'}
                  ${showSuperLike ? 'border-amber-400' : ''}`}
      style={{ y, opacity, scale }}
      drag="y"
      dragConstraints={{ top: -100, bottom: 0 }}
      dragElastic={0.1}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={handleDragEnd}
      onClick={() => !isDragging && onSelect(movie)}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, x: side === "left" ? -50 : 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.4 }}
      data-testid={`game-card-${side}`}
    >
      {/* Movie Poster */}
      {movie.poster_path ? (
        <img
          src={`${TMDB_IMG}w500${movie.poster_path}`}
          alt={movie.title}
          className="w-full h-full object-cover"
          draggable={false}
        />
      ) : (
        <div className="w-full h-full bg-chef-surface flex items-center justify-center">
          <span className="text-chef-muted">No Image</span>
        </div>
      )}

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

      {/* Super Like Indicator */}
      <AnimatePresence>
        {showSuperLike && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-amber-500/20 backdrop-blur-sm"
          >
            <div className="flex flex-col items-center gap-2">
              <Sparkles className="w-12 h-12 text-amber-400" />
              <span className="text-amber-400 font-bold text-lg">SUPER LIKE!</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Swipe Up Hint */}
      <motion.div
        className="absolute top-4 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 opacity-50"
        animate={{ y: [0, -5, 0] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
      >
        <ChevronUp className="w-5 h-5 text-amber-400" />
        <span className="text-[10px] text-amber-400 uppercase tracking-wider">Super Like</span>
      </motion.div>

      {/* Movie Info */}
      <div className="absolute bottom-0 left-0 right-0 p-4">
        <h3 className="font-serif text-lg md:text-xl text-white leading-tight line-clamp-2 mb-1">
          {movie.title}
        </h3>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-chef-teal text-sm">{movie.vote_average?.toFixed(1)}</span>
          <span className="text-chef-muted text-sm">
            {movie.release_date?.split("-")[0]}
          </span>
        </div>
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {movie.genres.slice(0, 2).map((genre, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 text-xs text-chef-muted bg-white/10 rounded-full"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tap Indicator */}
      <div className="absolute bottom-20 left-1/2 -translate-x-1/2">
        <span className="text-[10px] text-white/50 uppercase tracking-wider">Tap to select</span>
      </div>
    </motion.div>
  );
};

// Results Card Component
const ResultCard = ({ movie, rank }) => {
  if (!movie) return null;

  const medals = ["🥇", "🥈", "🥉"];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.2 }}
      className="flex gap-4 p-4 bg-chef-surface/50 border border-white/10 rounded-xl"
      data-testid={`result-card-${rank}`}
    >
      <div className="relative w-20 h-28 rounded-lg overflow-hidden flex-shrink-0">
        {movie.poster_path ? (
          <img
            src={`${TMDB_IMG}w200${movie.poster_path}`}
            alt={movie.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-chef-bg flex items-center justify-center">
            <span className="text-chef-muted text-xs">No Image</span>
          </div>
        )}
        <div className="absolute top-1 left-1 text-2xl">{medals[rank]}</div>
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="font-serif text-lg text-chef-platinum truncate">{movie.title}</h4>
        <p className="text-sm text-chef-muted mt-1 line-clamp-2">{movie.overview}</p>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-chef-teal font-medium">{movie.confidence}% Match</span>
          <span className="text-chef-muted text-sm">{movie.vote_average?.toFixed(1)} TMDB</span>
        </div>
        {movie.genres && (
          <div className="flex flex-wrap gap-1 mt-2">
            {movie.genres.slice(0, 3).map((g, i) => (
              <span key={i} className="text-xs text-chef-muted/70 bg-white/5 px-2 py-0.5 rounded">
                {g}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

// Main Movie Game Component
const MovieGame = ({ open, onOpenChange }) => {
  const [gameState, setGameState] = useState("idle"); // idle, playing, results
  const [sessionId, setSessionId] = useState(null);
  const [round, setRound] = useState(1);
  const [movies, setMovies] = useState([null, null]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [currentTop, setCurrentTop] = useState([]);

  const startGame = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/game/start`, {}, { headers: authHeaders() });
      setSessionId(res.data.session_id);
      setRound(res.data.round);
      setMovies(res.data.movies);
      setGameState("playing");
      setCurrentTop([]);
    } catch (error) {
      console.error("Failed to start game:", error);
      toast.error("Failed to start game. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (chosenMovie, isSuperLike = false) => {
    if (loading || !movies[0] || !movies[1]) return;

    const rejectedMovie = movies.find(m => m?.id !== chosenMovie.id);
    if (!rejectedMovie) return;

    setLoading(true);
    try {
      const res = await axios.post(`${API}/game/choose`, {
        session_id: sessionId,
        round_number: round,
        chosen_movie_id: chosenMovie.id,
        rejected_movie_id: rejectedMovie.id,
        is_super_like: isSuperLike
      }, { headers: authHeaders() });

      if (res.data.game_over) {
        setResults(res.data.recommendations);
        setGameState("results");
        toast.success(`Game complete in ${res.data.total_rounds} rounds!`);
      } else {
        setRound(res.data.round);
        setMovies(res.data.movies);
        setCurrentTop(res.data.current_top || []);
      }
    } catch (error) {
      console.error("Failed to submit choice:", error);
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    if (loading) return;

    setLoading(true);
    try {
      const res = await axios.post(
        `${API}/game/skip?session_id=${sessionId}&round_number=${round}`,
        {},
        { headers: authHeaders() }
      );

      if (res.data.game_over) {
        setResults(res.data.recommendations);
        setGameState("results");
      } else {
        setRound(res.data.round);
        setMovies(res.data.movies);
      }
    } catch (error) {
      console.error("Failed to skip:", error);
      toast.error("Failed to skip. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const resetGame = () => {
    setGameState("idle");
    setSessionId(null);
    setRound(1);
    setMovies([null, null]);
    setResults([]);
    setCurrentTop([]);
  };

  const handleClose = () => {
    resetGame();
    onOpenChange(false);
  };

  // Reset when modal closes
  useEffect(() => {
    if (!open) {
      resetGame();
    }
  }, [open]);

  if (!open) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={handleClose}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/90 backdrop-blur-md" />

      {/* Modal Content */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto
                   bg-chef-bg border border-white/10 rounded-2xl
                   shadow-cinematic"
        onClick={(e) => e.stopPropagation()}
        data-testid="movie-game-modal"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-4 
                        bg-chef-bg/80 backdrop-blur-xl border-b border-white/10">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-chef-teal" />
            <h2 className="font-serif text-xl text-chef-platinum">Movie Game</h2>
          </div>
          
          {gameState === "playing" && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-chef-muted">
                Round <span className="text-chef-platinum font-medium">{round}</span> / 20
              </span>
              {/* Progress bar */}
              <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-chef-teal"
                  initial={{ width: 0 }}
                  animate={{ width: `${(round / 20) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
          )}
          
          <button
            onClick={handleClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
            data-testid="game-close-btn"
          >
            <X className="w-5 h-5 text-chef-muted hover:text-chef-platinum" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Idle State - Start Screen */}
          {gameState === "idle" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-center"
            >
              <div className="w-20 h-20 rounded-full bg-chef-teal/10 border border-chef-teal/30
                            flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-chef-teal" />
              </div>
              
              <h3 className="font-serif text-2xl text-chef-platinum mb-3">
                Discover Your Perfect Movie
              </h3>
              <p className="text-chef-muted max-w-md mb-8">
                Choose between two movies in each round. We'll learn your preferences 
                and recommend the perfect films for you. Swipe up for a super-like!
              </p>
              
              <div className="flex flex-col gap-3 text-sm text-chef-muted/80 mb-8">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-chef-teal" />
                  <span>Tap a movie to select it (+1 point)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span>Swipe up for super-like (3x points)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-white/30" />
                  <span>Skip if you can't decide</span>
                </div>
              </div>
              
              <motion.button
                onClick={startGame}
                disabled={loading}
                className="px-8 py-3 bg-chef-teal/20 border border-chef-teal/30 
                         text-chef-teal rounded-full font-medium
                         hover:bg-chef-teal/30 transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                data-testid="start-game-btn"
              >
                {loading ? "Starting..." : "Start Game"}
              </motion.button>
            </motion.div>
          )}

          {/* Playing State */}
          {gameState === "playing" && (
            <div className="flex flex-col items-center">
              {/* Current Top Picks Preview */}
              {currentTop.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 text-center"
                >
                  <p className="text-xs text-chef-muted/60 uppercase tracking-wider mb-2">
                    Current Top Picks
                  </p>
                  <div className="flex gap-3 justify-center">
                    {currentTop.slice(0, 3).map((m, i) => (
                      <span key={i} className="text-xs text-chef-muted">
                        {m.title} ({m.confidence}%)
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Movie Cards */}
              <div className="flex items-center justify-center gap-6 w-full mb-8">
                <AnimatePresence mode="wait">
                  <SwipeableCard
                    key={`left-${round}`}
                    movie={movies[0]}
                    onSelect={(m) => handleSelect(m, false)}
                    onSuperLike={(m) => handleSelect(m, true)}
                    side="left"
                    isActive={!loading}
                  />
                  
                  <div className="text-chef-muted/50 font-serif text-2xl">vs</div>
                  
                  <SwipeableCard
                    key={`right-${round}`}
                    movie={movies[1]}
                    onSelect={(m) => handleSelect(m, false)}
                    onSuperLike={(m) => handleSelect(m, true)}
                    side="right"
                    isActive={!loading}
                  />
                </AnimatePresence>
              </div>

              {/* Skip Button */}
              <motion.button
                onClick={handleSkip}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 
                         bg-white/5 border border-white/10 rounded-full
                         text-chef-muted hover:text-chef-platinum hover:bg-white/10
                         transition-all disabled:opacity-50"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                data-testid="skip-btn"
              >
                <SkipForward className="w-4 h-4" />
                <span className="text-sm">Skip</span>
              </motion.button>

              {loading && (
                <div className="mt-4 text-chef-muted text-sm animate-pulse">
                  Loading next round...
                </div>
              )}
            </div>
          )}

          {/* Results State */}
          {gameState === "results" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center"
            >
              <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/30
                            flex items-center justify-center mb-6">
                <Trophy className="w-8 h-8 text-amber-400" />
              </div>
              
              <h3 className="font-serif text-2xl text-chef-platinum mb-2">
                Your Perfect Movies
              </h3>
              <p className="text-chef-muted mb-8">
                Based on your choices, here are our top recommendations
              </p>

              <div className="w-full max-w-xl space-y-4 mb-8">
                {results.map((movie, index) => (
                  <ResultCard key={movie.id} movie={movie} rank={index} />
                ))}
              </div>

              <motion.button
                onClick={resetGame}
                className="flex items-center gap-2 px-6 py-3 
                         bg-chef-teal/20 border border-chef-teal/30 rounded-full
                         text-chef-teal hover:bg-chef-teal/30 transition-all"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                data-testid="play-again-btn"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Play Again</span>
              </motion.button>
            </motion.div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default MovieGame;
