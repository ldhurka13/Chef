import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform } from "framer-motion";
import { X, SkipForward, Sparkles, Trophy, RotateCcw, ChevronUp, HelpCircle, Crown } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TMDB_IMG = "https://image.tmdb.org/t/p/";

const getToken = () => localStorage.getItem("chef_token");
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

// Swipeable Movie Card Component with King indicator
const SwipeableCard = ({ movie, onSelect, onSuperLike, side, isKing, isActive, roundStartTime }) => {
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
      const reactionTime = Date.now() - roundStartTime;
      setTimeout(() => {
        onSuperLike(movie, reactionTime);
      }, 300);
    }
  };

  const handleClick = () => {
    if (!isDragging && isActive) {
      const reactionTime = Date.now() - roundStartTime;
      onSelect(movie, reactionTime);
    }
  };

  if (!movie) return null;

  return (
    <motion.div
      ref={cardRef}
      className={`relative flex-1 max-w-[45%] aspect-[2/3] rounded-2xl overflow-hidden cursor-pointer
                  border-2 transition-colors duration-300
                  ${isKing ? 'border-amber-400/50 ring-2 ring-amber-400/20' : 'border-white/10'}
                  ${isActive ? 'hover:border-chef-teal/50' : 'opacity-70'}
                  ${showSuperLike ? 'border-amber-400' : ''}`}
      style={{ y, opacity, scale }}
      drag={isActive ? "y" : false}
      dragConstraints={{ top: -100, bottom: 0 }}
      dragElastic={0.1}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      whileHover={isActive ? { scale: 1.02 } : {}}
      whileTap={isActive ? { scale: 0.98 } : {}}
      initial={{ opacity: 0, x: side === "left" ? -50 : 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.4 }}
      data-testid={`game-card-${side}`}
    >
      {/* King Crown Badge */}
      {isKing && (
        <motion.div
          initial={{ scale: 0, y: -20 }}
          animate={{ scale: 1, y: 0 }}
          className="absolute top-3 left-3 z-20 flex items-center gap-1 px-2 py-1 
                     bg-amber-500/20 border border-amber-400/30 rounded-full"
        >
          <Crown className="w-4 h-4 text-amber-400" />
          <span className="text-xs text-amber-400 font-medium">King</span>
        </motion.div>
      )}

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
      {isActive && !isKing && (
        <motion.div
          className="absolute top-3 right-3 flex flex-col items-center gap-1 opacity-50"
          animate={{ y: [0, -5, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          <ChevronUp className="w-5 h-5 text-amber-400" />
          <span className="text-[10px] text-amber-400 uppercase tracking-wider">Super</span>
        </motion.div>
      )}

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
      {isActive && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2">
          <span className="text-[10px] text-white/50 uppercase tracking-wider">Tap to select</span>
        </div>
      )}
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
      </div>
    </motion.div>
  );
};

// Reaction Time Indicator
const ReactionIndicator = ({ reactionTime }) => {
  if (!reactionTime) return null;
  
  const seconds = (reactionTime / 1000).toFixed(1);
  const isFast = reactionTime < 2000;
  const isSlow = reactionTime > 5000;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`text-xs px-2 py-1 rounded-full ${
        isFast ? 'bg-emerald-500/20 text-emerald-400' :
        isSlow ? 'bg-red-500/20 text-red-400' :
        'bg-white/10 text-chef-muted'
      }`}
    >
      {seconds}s {isFast ? '⚡ Fast!' : isSlow ? '🤔 Hesitant' : ''}
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
  const [currentScores, setCurrentScores] = useState([]);
  const [kingPosition, setKingPosition] = useState(null);
  const [roundStartTime, setRoundStartTime] = useState(null);
  const [lastReactionTime, setLastReactionTime] = useState(null);

  const startGame = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/game/start`, {}, { headers: authHeaders() });
      setSessionId(res.data.session_id);
      setRound(res.data.round);
      setMovies(res.data.movies);
      setKingPosition(res.data.king_position);
      setGameState("playing");
      setCurrentScores([]);
      setRoundStartTime(Date.now());
      setLastReactionTime(null);
    } catch (error) {
      console.error("Failed to start game:", error);
      toast.error("Failed to start game. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (chosenMovie, reactionTime, isSuperLike = false) => {
    if (loading || !movies[0] || !movies[1]) return;

    const rejectedMovie = movies.find(m => m?.id !== chosenMovie.id);
    if (!rejectedMovie) return;

    setLoading(true);
    setLastReactionTime(reactionTime);

    try {
      const res = await axios.post(`${API}/game/choose`, {
        session_id: sessionId,
        round_number: round,
        chosen_movie_id: chosenMovie.id,
        rejected_movie_id: rejectedMovie.id,
        reaction_time_ms: reactionTime,
        is_super_like: isSuperLike,
        is_cant_decide: false
      }, { headers: authHeaders() });

      if (res.data.game_over) {
        setResults(res.data.recommendations);
        setGameState("results");
        toast.success(`Game complete in ${res.data.total_rounds} rounds!`);
      } else {
        setRound(res.data.round);
        setMovies(res.data.movies);
        setKingPosition(res.data.king_position);
        setCurrentScores(res.data.current_scores || []);
        setRoundStartTime(Date.now());
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
        setKingPosition(res.data.king_position);
        setCurrentScores(res.data.current_scores || []);
        setRoundStartTime(Date.now());
        setLastReactionTime(null);
      }
    } catch (error) {
      console.error("Failed to skip:", error);
      toast.error("Failed to skip. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCantDecide = async () => {
    if (loading || !movies[0] || !movies[1]) return;

    const reactionTime = Date.now() - roundStartTime;
    setLoading(true);
    setLastReactionTime(reactionTime);

    try {
      const res = await axios.post(
        `${API}/game/cant-decide?session_id=${sessionId}&round_number=${round}&movie1_id=${movies[0].id}&movie2_id=${movies[1].id}&reaction_time_ms=${reactionTime}`,
        {},
        { headers: authHeaders() }
      );

      if (res.data.game_over) {
        setResults(res.data.recommendations);
        setGameState("results");
      } else {
        setRound(res.data.round);
        setMovies(res.data.movies);
        setKingPosition(res.data.king_position);
        setCurrentScores(res.data.current_scores || []);
        setRoundStartTime(Date.now());
      }
    } catch (error) {
      console.error("Failed to submit can't decide:", error);
      toast.error("Something went wrong. Please try again.");
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
    setCurrentScores([]);
    setKingPosition(null);
    setRoundStartTime(null);
    setLastReactionTime(null);
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
            <Crown className="w-6 h-6 text-amber-400" />
            <h2 className="font-serif text-xl text-chef-platinum">King of the Hill</h2>
          </div>
          
          {gameState === "playing" && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-chef-muted">
                Round <span className="text-chef-platinum font-medium">{round}</span> / 10
              </span>
              {/* Progress bar */}
              <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-amber-400"
                  initial={{ width: 0 }}
                  animate={{ width: `${(round / 10) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              {lastReactionTime && <ReactionIndicator reactionTime={lastReactionTime} />}
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
              <div className="w-20 h-20 rounded-full bg-amber-500/10 border border-amber-400/30
                            flex items-center justify-center mb-6">
                <Crown className="w-10 h-10 text-amber-400" />
              </div>
              
              <h3 className="font-serif text-2xl text-chef-platinum mb-3">
                King of the Hill
              </h3>
              <p className="text-chef-muted max-w-md mb-8">
                Choose between two movies - the winner stays to face a new challenger! 
                Fast choices show strong preferences. Swipe up for super-like!
              </p>
              
              <div className="flex flex-col gap-3 text-sm text-chef-muted/80 mb-8">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-chef-teal" />
                  <span>Tap a movie to select it - faster = higher score</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span>Swipe up for super-like (2x multiplier)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400" />
                  <span>Can't Decide = equal points to both</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-white/30" />
                  <span>Skip = 0 points, fresh matchup</span>
                </div>
              </div>
              
              <motion.button
                onClick={startGame}
                disabled={loading}
                className="px-8 py-3 bg-amber-500/20 border border-amber-400/30 
                         text-amber-400 rounded-full font-medium
                         hover:bg-amber-500/30 transition-all
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
              {/* Current Scores Preview */}
              {currentScores.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 text-center"
                >
                  <p className="text-xs text-chef-muted/60 uppercase tracking-wider mb-2">
                    Current Leaders
                  </p>
                  <div className="flex gap-4 justify-center">
                    {currentScores.slice(0, 3).map((m, i) => (
                      <span key={i} className="text-xs text-chef-muted bg-white/5 px-2 py-1 rounded">
                        {i + 1}. {m.title?.substring(0, 15)}... ({m.score})
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Movie Cards */}
              <div className="flex items-center justify-center gap-6 w-full mb-8">
                <AnimatePresence mode="wait">
                  <SwipeableCard
                    key={`left-${round}-${movies[0]?.id}`}
                    movie={movies[0]}
                    onSelect={(m, rt) => handleSelect(m, rt, false)}
                    onSuperLike={(m, rt) => handleSelect(m, rt, true)}
                    side="left"
                    isKing={kingPosition === "left"}
                    isActive={!loading}
                    roundStartTime={roundStartTime}
                  />
                  
                  <div className="text-chef-muted/50 font-serif text-2xl">vs</div>
                  
                  <SwipeableCard
                    key={`right-${round}-${movies[1]?.id}`}
                    movie={movies[1]}
                    onSelect={(m, rt) => handleSelect(m, rt, false)}
                    onSuperLike={(m, rt) => handleSelect(m, rt, true)}
                    side="right"
                    isKing={kingPosition === "right"}
                    isActive={!loading}
                    roundStartTime={roundStartTime}
                  />
                </AnimatePresence>
              </div>

              {/* Control Buttons */}
              <div className="flex items-center gap-4">
                <motion.button
                  onClick={handleSkip}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 
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

                <motion.button
                  onClick={handleCantDecide}
                  disabled={loading}
                  className="flex items-center gap-2 px-5 py-2.5 
                           bg-purple-500/10 border border-purple-400/20 rounded-full
                           text-purple-400 hover:bg-purple-500/20
                           transition-all disabled:opacity-50"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  data-testid="cant-decide-btn"
                >
                  <HelpCircle className="w-4 h-4" />
                  <span className="text-sm">Can't Decide</span>
                </motion.button>
              </div>

              {loading && (
                <div className="mt-4 text-chef-muted text-sm animate-pulse">
                  Loading next challenger...
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
                Based on your choices and reaction times
              </p>

              <div className="w-full max-w-xl space-y-4 mb-8">
                {results.map((movie, index) => (
                  <ResultCard key={movie.id} movie={movie} rank={index} />
                ))}
              </div>

              <motion.button
                onClick={resetGame}
                className="flex items-center gap-2 px-6 py-3 
                         bg-amber-500/20 border border-amber-400/30 rounded-full
                         text-amber-400 hover:bg-amber-500/30 transition-all"
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
