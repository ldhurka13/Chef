import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Plus, Check, Film, Loader2, Trash2, Calendar, Star, X
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const WatchHistoryPage = ({ user }) => {
  const navigate = useNavigate();
  const debounceRef = useRef(null);

  const [watchHistory, setWatchHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [addingMovie, setAddingMovie] = useState(null);
  const [addRating, setAddRating] = useState(7.0);
  const [addDate, setAddDate] = useState(new Date().toISOString().split("T")[0]);

  const getToken = () => localStorage.getItem("chef_token");
  const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    const token = getToken();
    if (!token) { setLoading(false); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API}/user/watch-history`, { headers: authHeaders() });
      setWatchHistory(res.data || []);
    } catch {} finally { setLoading(false); }
  };

  const handleSearch = useCallback((q) => {
    setQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (q.length < 2) { setResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await axios.get(`${API}/movies/search-tmdb?query=${encodeURIComponent(q)}`);
        setResults(res.data.results || []);
      } catch { setResults([]); }
      finally { setSearching(false); }
    }, 350);
  }, []);

  const handleSelect = (movie) => {
    setAddingMovie(movie);
    setAddRating(7.0);
    setAddDate(new Date().toISOString().split("T")[0]);
    setQuery("");
    setResults([]);
  };

  const handleAdd = async () => {
    if (!addingMovie) return;
    try {
      await axios.post(`${API}/user/watch-history`, {
        tmdb_id: addingMovie.id,
        user_rating: addRating,
        watched_date: addDate,
        title: addingMovie.title,
        poster_path: addingMovie.poster_url ? addingMovie.poster_url.split("/").pop() : null,
      }, { headers: authHeaders() });
      toast.success(`Added "${addingMovie.title}"`);
      setAddingMovie(null);
      fetchHistory();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    }
  };

  const handleRemove = async (tmdbId, title) => {
    try {
      await axios.delete(`${API}/user/watch-history/${tmdbId}`, { headers: authHeaders() });
      setWatchHistory((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
      toast.success(`Removed "${title}"`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to remove");
    }
  };

  if (!user) {
    return (
      <main className="pb-24 pt-20 px-4 md:px-8">
        <div className="max-w-3xl mx-auto text-center py-20">
          <Film className="w-12 h-12 text-chef-muted/30 mx-auto mb-4" />
          <h2 className="font-serif text-2xl text-chef-platinum mb-2">Sign in to view your history</h2>
          <p className="text-sm text-chef-muted mb-6">Log in to track and manage your watched movies.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 rounded-full bg-chef-teal/10 border border-chef-teal/20
                     text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
          >
            Go Home
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="pb-24 pt-20 px-4 md:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-serif text-3xl md:text-4xl tracking-tight text-chef-platinum mb-2">
          Watch History
        </h1>
        <p className="text-sm text-chef-muted mb-8">
          {watchHistory.length} movie{watchHistory.length !== 1 ? "s" : ""} tracked
        </p>

        {/* Search to add */}
        <div className="relative mb-6">
          <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10
                        rounded-lg px-4 py-3">
            <Search className="w-4 h-4 text-chef-muted/40" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search a movie to add to your history..."
              className="flex-1 bg-transparent text-sm text-chef-platinum
                       placeholder:text-chef-muted/30 focus:outline-none"
              data-testid="history-search-input"
            />
            {searching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
          </div>
          {results.length > 0 && !addingMovie && (
            <div className="absolute left-0 right-0 top-full mt-1 z-20
                          bg-chef-surface/95 backdrop-blur-xl border border-white/10
                          rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
              {results.map((m) => {
                const inHistory = watchHistory.some((h) => h.tmdb_id === m.id);
                return (
                  <button
                    key={m.id}
                    onClick={() => handleSelect(m)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors
                      ${inHistory ? "opacity-50" : "hover:bg-white/5"}`}
                    data-testid={`history-result-${m.id}`}
                  >
                    {m.poster_url ? (
                      <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                    ) : (
                      <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                      <p className="text-xs text-chef-muted">{m.year}</p>
                    </div>
                    {inHistory && <span className="text-xs text-chef-teal">In history</span>}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Add movie form */}
        <AnimatePresence>
          {addingMovie && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 bg-chef-surface/60 border border-chef-teal/20 rounded-lg p-5 overflow-hidden"
            >
              <div className="flex items-start gap-4">
                {addingMovie.poster_url ? (
                  <img src={addingMovie.poster_url} alt="" className="w-16 h-24 rounded object-cover flex-shrink-0" />
                ) : (
                  <div className="w-16 h-24 rounded bg-chef-bg flex-shrink-0 flex items-center justify-center">
                    <Film className="w-5 h-5 text-chef-muted/30" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-base text-chef-platinum font-medium truncate">{addingMovie.title}</p>
                  <p className="text-xs text-chef-muted mb-4">{addingMovie.year}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">
                        Your Rating: <span className="text-chef-gold font-medium text-sm">{addRating.toFixed(1)}</span>/10
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="0.1"
                        value={addRating}
                        onChange={(e) => setAddRating(parseFloat(e.target.value))}
                        className="w-full accent-chef-gold"
                        data-testid="history-rating-slider"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">Watch Date</label>
                      <input
                        type="date"
                        value={addDate}
                        onChange={(e) => setAddDate(e.target.value)}
                        max={new Date().toISOString().split("T")[0]}
                        className="w-full bg-chef-bg/80 border border-white/10 rounded-lg px-3 py-2
                                 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40
                                 [color-scheme:dark]"
                        data-testid="history-date-input"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={handleAdd}
                      className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-chef-teal/10 border border-chef-teal/20
                               text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
                      data-testid="confirm-add-history-btn"
                    >
                      <Check className="w-3.5 h-3.5" /> Add to History
                    </button>
                    <button
                      onClick={() => setAddingMovie(null)}
                      className="px-4 py-2.5 rounded-lg text-sm text-chef-muted hover:text-chef-platinum
                               hover:bg-white/5 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History list */}
        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-6 h-6 text-chef-teal animate-spin" />
          </div>
        ) : watchHistory.length > 0 ? (
          <div className="space-y-2">
            {watchHistory.map((item) => (
              <motion.div
                key={item.tmdb_id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-4 px-4 py-3 rounded-lg bg-chef-surface/40
                         border border-white/5 hover:border-white/10 transition-colors group"
                data-testid={`history-item-${item.tmdb_id}`}
              >
                {item.poster_path ? (
                  <img
                    src={`https://image.tmdb.org/t/p/w92${item.poster_path}`}
                    alt=""
                    className="w-10 h-15 rounded object-cover flex-shrink-0"
                  />
                ) : (
                  <div className="w-10 h-15 rounded bg-chef-bg flex-shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-chef-platinum truncate font-medium">{item.title}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-xs text-chef-gold">
                      <Star className="w-3 h-3" fill="currentColor" />
                      {(item.user_rating || 0).toFixed(1)}
                    </span>
                    {item.last_watched_date && (
                      <span className="flex items-center gap-1 text-xs text-chef-muted">
                        <Calendar className="w-3 h-3" />
                        {item.last_watched_date}
                      </span>
                    )}
                    {item.watch_count > 1 && (
                      <span className="text-xs text-chef-muted/60">{item.watch_count}x</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleRemove(item.tmdb_id, item.title)}
                  className="p-2 rounded-lg text-chef-muted/30 hover:text-red-400
                           hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100"
                  data-testid={`remove-history-${item.tmdb_id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Film className="w-10 h-10 text-chef-muted/20 mx-auto mb-3" />
            <p className="text-sm text-chef-muted/50">No movies in your history yet</p>
            <p className="text-xs text-chef-muted/30 mt-1">Search above to start tracking!</p>
          </div>
        )}
      </div>
    </main>
  );
};

export default WatchHistoryPage;
