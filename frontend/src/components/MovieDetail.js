import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Star, Clock, Calendar, Plus, Check, Play, Tv, ExternalLink, Bookmark } from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const getToken = () => localStorage.getItem("chef_token");

// Get user's country code from browser locale
const getUserCountry = () => {
  try {
    const parts = (navigator.language || "en-US").split("-");
    if (parts.length >= 2) return parts[1].toLowerCase();
  } catch {}
  return "us";
};

const StreamingBadge = ({ type }) => {
  const labels = {
    subscription: "Stream",
    free: "Free",
    addon: "Add-on",
    rent: "Rent",
    buy: "Buy",
  };
  const colors = {
    subscription: "bg-chef-teal/20 text-chef-teal border-chef-teal/30",
    free: "bg-green-500/20 text-green-400 border-green-500/30",
    addon: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    rent: "bg-chef-gold/20 text-chef-gold border-chef-gold/30",
    buy: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  };
  return (
    <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 border rounded-full ${colors[type] || colors.subscription}`}>
      {labels[type] || type}
    </span>
  );
};

const MovieDetail = ({ open, onOpenChange, movie, onAddToHistory, userCountry }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userRating, setUserRating] = useState(7);
  const [showRatingInput, setShowRatingInput] = useState(false);
  const [streamingOptions, setStreamingOptions] = useState([]);
  const [streamingLoading, setStreamingLoading] = useState(false);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistLoading, setWatchlistLoading] = useState(false);

  useEffect(() => {
    if (open && movie?.id) {
      fetchDetails(movie.id);
      fetchStreaming(movie.id);
      checkWatchlist(movie.id);
    }
    if (!open) {
      setStreamingOptions([]);
      setShowRatingInput(false);
      setInWatchlist(false);
    }
  }, [open, movie]);

  const fetchDetails = async (movieId) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/movies/${movieId}`);
      setDetails(res.data);
    } catch (error) {
      console.error("Failed to fetch movie details:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStreaming = async (movieId) => {
    setStreamingLoading(true);
    try {
      const country = userCountry || getUserCountry();
      const res = await axios.get(`${API}/movies/${movieId}/streaming?country=${country}`);
      setStreamingOptions(res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch streaming info:", error);
      setStreamingOptions([]);
    } finally {
      setStreamingLoading(false);
    }
  };

  const handleAddToHistory = () => {
    if (details) {
      onAddToHistory(details, userRating);
      setShowRatingInput(false);
    }
  };

  const checkWatchlist = async (movieId) => {
    const token = getToken();
    if (!token) return;
    try {
      const res = await axios.get(`${API}/user/watchlist/check/${movieId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInWatchlist(res.data.in_watchlist);
    } catch {}
  };

  const handleToggleWatchlist = async () => {
    const token = getToken();
    if (!token) return;
    setWatchlistLoading(true);
    try {
      if (inWatchlist) {
        await axios.delete(`${API}/user/watchlist/${data.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInWatchlist(false);
      } else {
        await axios.post(`${API}/user/watchlist`, {
          tmdb_id: data.id,
          title: data.title,
          poster_path: data.poster_path,
          release_date: data.release_date,
          vote_average: data.vote_average,
          genres: data.genres || [],
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInWatchlist(true);
      }
    } catch {}
    setWatchlistLoading(false);
  };

  const data = details || movie;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[70] overflow-y-auto"
          onClick={() => onOpenChange(false)}
        >
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/90 backdrop-blur-sm" />
          
          {/* Content */}
          <div className="relative min-h-screen flex items-start justify-center py-8 px-4">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ duration: 0.4 }}
              className="relative w-full max-w-4xl rounded-3xl overflow-hidden
                         bg-chef-surface border border-white/10 shadow-cinematic"
              onClick={(e) => e.stopPropagation()}
              data-testid="movie-detail-modal"
            >
              {/* Close Button */}
              <button
                onClick={() => onOpenChange(false)}
                className="absolute top-4 right-4 z-10 p-2 rounded-full
                           bg-black/50 backdrop-blur-sm
                           hover:bg-black/70 transition-colors"
                data-testid="detail-close-btn"
              >
                <X className="w-5 h-5 text-chef-platinum" strokeWidth={1.5} />
              </button>

              {loading ? (
                <div className="h-96 flex items-center justify-center">
                  <div className="w-8 h-8 border-2 border-chef-teal border-t-transparent rounded-full animate-spin" />
                </div>
              ) : data ? (
                <>
                  {/* Backdrop Image */}
                  <div className="relative h-64 md:h-80">
                    {data.backdrop_url ? (
                      <img
                        src={data.backdrop_url}
                        alt={data.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-chef-surface-highlight" />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-chef-surface via-chef-surface/50 to-transparent" />
                    
                    {/* Trailer Button */}
                    {details?.trailer_url && (
                      <a
                        href={details.trailer_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                                   w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm
                                   flex items-center justify-center
                                   hover:bg-white/30 hover:scale-110
                                   transition-all duration-300"
                        data-testid="trailer-btn"
                      >
                        <Play className="w-8 h-8 text-white ml-1" fill="white" />
                      </a>
                    )}
                  </div>

                  {/* Content */}
                  <div className="px-6 md:px-10 pb-10 -mt-20 relative">
                    <div className="flex gap-6">
                      {/* Poster */}
                      <div className="hidden md:block flex-shrink-0 w-40 -mt-10">
                        {data.poster_url ? (
                          <img
                            src={data.poster_url}
                            alt={data.title}
                            className="w-full rounded-xl shadow-cinematic"
                          />
                        ) : (
                          <div className="w-full aspect-[2/3] bg-chef-surface-highlight rounded-xl" />
                        )}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-4">
                          {data.title}
                        </h2>

                        {/* Meta */}
                        <div className="flex flex-wrap items-center gap-4 mb-6 text-chef-muted">
                          {data.vote_average && (
                            <div className="flex items-center gap-1">
                              <Star className="w-4 h-4 text-chef-gold" fill="#C0B283" />
                              <span>{data.vote_average.toFixed(1)}</span>
                            </div>
                          )}
                          {details?.runtime && (
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" strokeWidth={1.5} />
                              <span>{details.runtime} min</span>
                            </div>
                          )}
                          {data.release_date && (
                            <div className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" strokeWidth={1.5} />
                              <span>{data.release_date?.slice(0, 4)}</span>
                            </div>
                          )}
                        </div>

                        {/* Genres */}
                        {data.genres && data.genres.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-6">
                            {data.genres.map((genre, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1 text-xs uppercase tracking-wide
                                           bg-white/5 border border-white/10 rounded-full"
                              >
                                {genre}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Match & Vibe */}
                        {(data.match_percentage || data.vibe_tag) && (
                          <div className="flex items-center gap-4 mb-6">
                            {data.match_percentage && (
                              <span className="text-chef-teal font-medium">
                                {data.match_percentage}% Match
                              </span>
                            )}
                            {data.vibe_tag && (
                              <span className="text-chef-gold italic">
                                {data.vibe_tag}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Overview */}
                        {data.overview && (
                          <p className="text-chef-muted leading-relaxed mb-8">
                            {data.overview}
                          </p>
                        )}

                        {/* Actions */}
                        <div className="flex flex-wrap gap-3">
                          {/* Watchlist Button */}
                          <button
                            onClick={handleToggleWatchlist}
                            disabled={watchlistLoading}
                            className={`flex items-center gap-2 px-5 py-3 rounded-full border transition-colors
                              ${inWatchlist
                                ? "bg-chef-teal/20 border-chef-teal/30 text-chef-teal"
                                : "bg-white/5 border-white/10 text-chef-muted hover:text-chef-platinum hover:border-white/20"
                              }`}
                            data-testid="toggle-watchlist-btn"
                          >
                            <Bookmark className="w-4 h-4" fill={inWatchlist ? "currentColor" : "none"} />
                            <span>{inWatchlist ? "In Watchlist" : "Add to Watchlist"}</span>
                          </button>

                          {details?.in_history ? (
                            <div className="flex items-center gap-2 px-6 py-3 rounded-full
                                          bg-chef-teal/20 border border-chef-teal/30
                                          text-chef-teal">
                              <Check className="w-4 h-4" />
                              <span>In your history (rated {details.user_rating}/10)</span>
                            </div>
                          ) : (
                            <>
                              {showRatingInput ? (
                                <div className="flex items-center gap-3">
                                  <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={userRating}
                                    onChange={(e) => setUserRating(parseInt(e.target.value))}
                                    className="w-32"
                                  />
                                  <span className="text-chef-gold font-serif text-xl w-8">
                                    {userRating}
                                  </span>
                                  <button
                                    onClick={handleAddToHistory}
                                    className="px-4 py-2 rounded-full bg-chef-teal/20 
                                             border border-chef-teal/30 text-chef-teal
                                             hover:bg-chef-teal/30 transition-colors"
                                    data-testid="confirm-rating-btn"
                                  >
                                    Save
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => setShowRatingInput(true)}
                                  className="flex items-center gap-2 px-6 py-3 rounded-full
                                           bg-chef-gold/10 border border-chef-gold/30
                                           text-chef-gold hover:bg-chef-gold/20
                                           transition-colors"
                                  data-testid="add-to-history-btn"
                                >
                                  <Plus className="w-4 h-4" />
                                  <span>Add to Watch History</span>
                                </button>
                              )}
                            </>
                          )}
                        </div>

                        {/* Where to Watch */}
                        <div className="mt-8" data-testid="where-to-watch">
                          <div className="flex items-center gap-2 mb-4">
                            <Tv className="w-4 h-4 text-chef-muted" strokeWidth={1.5} />
                            <h3 className="font-serif text-lg text-chef-platinum">Where to Watch</h3>
                          </div>
                          
                          {streamingLoading ? (
                            <div className="flex gap-3">
                              {[0, 1, 2].map((i) => (
                                <div key={i} className="h-14 w-36 rounded-lg skeleton" />
                              ))}
                            </div>
                          ) : streamingOptions.length > 0 ? (
                            <div className="flex flex-wrap gap-3">
                              {streamingOptions.map((opt, idx) => (
                                <a
                                  key={idx}
                                  href={opt.link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-3 px-4 py-3 rounded-lg
                                           bg-chef-bg/80 border border-white/5
                                           hover:border-white/20 hover:bg-chef-bg
                                           transition-all duration-200 group"
                                  data-testid={`streaming-${opt.service_id}`}
                                >
                                  <div
                                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                    style={{ backgroundColor: opt.service_color }}
                                  />
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="text-sm text-chef-platinum font-medium">
                                        {opt.service_name}
                                      </span>
                                      <ExternalLink className="w-3 h-3 text-chef-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5">
                                      <StreamingBadge type={opt.type} />
                                      {opt.price && (
                                        <span className="text-xs text-chef-muted">{opt.price}</span>
                                      )}
                                    </div>
                                  </div>
                                </a>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-chef-muted/60">
                              No streaming options found for your region
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Cast */}
                    {details?.cast && details.cast.length > 0 && (
                      <div className="mt-10">
                        <h3 className="font-serif text-xl mb-4">Cast</h3>
                        <div className="flex gap-4 overflow-x-auto pb-4 -mx-6 px-6 md:mx-0 md:px-0">
                          {details.cast.slice(0, 8).map((person, idx) => (
                            <div key={idx} className="flex-shrink-0 w-20 text-center">
                              {person.profile_url ? (
                                <img
                                  src={person.profile_url}
                                  alt={person.name}
                                  className="w-16 h-16 mx-auto rounded-full object-cover mb-2"
                                />
                              ) : (
                                <div className="w-16 h-16 mx-auto rounded-full bg-chef-surface-highlight mb-2" />
                              )}
                              <p className="text-xs text-chef-platinum truncate">
                                {person.name}
                              </p>
                              <p className="text-xs text-chef-muted truncate">
                                {person.character}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Similar Movies */}
                    {details?.similar && details.similar.length > 0 && (
                      <div className="mt-10">
                        <h3 className="font-serif text-xl mb-4">Similar Movies</h3>
                        <div className="flex gap-4 overflow-x-auto pb-4 -mx-6 px-6 md:mx-0 md:px-0">
                          {details.similar.map((similar, idx) => (
                            <div 
                              key={idx} 
                              className="flex-shrink-0 w-28 cursor-pointer group"
                              onClick={() => {
                                fetchDetails(similar.id);
                                fetchStreaming(similar.id);
                              }}
                            >
                              {similar.poster_url ? (
                                <img
                                  src={similar.poster_url}
                                  alt={similar.title}
                                  className="w-full aspect-[2/3] rounded-lg object-cover 
                                           group-hover:ring-2 ring-chef-teal/50 transition-all"
                                />
                              ) : (
                                <div className="w-full aspect-[2/3] rounded-lg bg-chef-surface-highlight" />
                              )}
                              <p className="text-xs text-chef-muted mt-2 truncate">
                                {similar.title}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="h-96 flex items-center justify-center">
                  <p className="text-chef-muted">No movie data available</p>
                </div>
              )}
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default MovieDetail;
