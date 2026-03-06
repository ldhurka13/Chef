import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Plus, Check, Film, Loader2, Trash2, Calendar, Star, X,
  BookOpen, Bookmark, User, Clapperboard, Users, Heart, MessageSquare, Pencil, RotateCcw
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TABS = [
  { id: "diary", label: "Diary", icon: BookOpen },
  { id: "watchlist", label: "Watchlist", icon: Bookmark },
  { id: "profile", label: "Profile", icon: User },
];

const getToken = () => localStorage.getItem("chef_token");
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

// ========== DIARY DETAIL MODAL ==========
const DiaryDetailModal = ({ movie, onClose, onMovieUpdated, onMovieRemoved }) => {
  const [watches, setWatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editRating, setEditRating] = useState(7.0);
  const [editDate, setEditDate] = useState("");
  const [editComment, setEditComment] = useState("");
  const [addingNew, setAddingNew] = useState(false);
  const [newRating, setNewRating] = useState(7.0);
  const [newDate, setNewDate] = useState(new Date().toISOString().split("T")[0]);
  const [newComment, setNewComment] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (movie?.watches) {
      // Descending order (latest first)
      const sorted = [...movie.watches].sort((a, b) => (b.date || "").localeCompare(a.date || ""));
      setWatches(sorted);
    }
  }, [movie]);

  const refreshMovie = async () => {
    try {
      const res = await axios.get(`${API}/user/watch-history`, { headers: authHeaders() });
      const updated = (res.data || []).find((m) => m.tmdb_id === movie.tmdb_id);
      if (updated) {
        const sorted = [...(updated.watches || [])].sort((a, b) => (b.date || "").localeCompare(a.date || ""));
        setWatches(sorted);
        onMovieUpdated(updated);
      } else {
        onMovieRemoved(movie.tmdb_id);
        onClose();
      }
    } catch {}
  };

  const handleAddWatch = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/user/watch-history/${movie.tmdb_id}/watches`, {
        rating: newRating,
        date: newDate,
        comment: newComment,
      }, { headers: authHeaders() });
      toast.success("Watch added");
      setAddingNew(false);
      setNewRating(7.0);
      setNewDate(new Date().toISOString().split("T")[0]);
      setNewComment("");
      await refreshMovie();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add watch");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (w) => {
    setEditingId(w.id);
    setEditRating(w.rating || 7.0);
    setEditDate(w.date || "");
    setEditComment(w.comment || "");
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/user/watch-history/${movie.tmdb_id}/watches/${editingId}`, {
        rating: editRating,
        date: editDate,
        comment: editComment,
      }, { headers: authHeaders() });
      toast.success("Watch updated");
      setEditingId(null);
      await refreshMovie();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteWatch = async (watchId) => {
    try {
      const res = await axios.delete(`${API}/user/watch-history/${movie.tmdb_id}/watches/${watchId}`, {
        headers: authHeaders(),
      });
      if (res.data?.removed) {
        toast.success("Movie removed from diary");
        onMovieRemoved(movie.tmdb_id);
        onClose();
      } else {
        toast.success("Watch removed");
        await refreshMovie();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete");
    }
  };

  const getWatchLabel = (index, total) => {
    // index is in descending array, so last item (index = total-1) is the earliest = First Watch
    const chronoIndex = total - 1 - index;
    if (chronoIndex === 0) return "First Watch";
    return `Re-watch #${chronoIndex}`;
  };

  if (!movie) return null;

  const posterUrl = movie.poster_path
    ? `https://image.tmdb.org/t/p/w342${movie.poster_path}`
    : null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] overflow-y-auto"
      onClick={onClose}
    >
      <div className="fixed inset-0 bg-black/90 backdrop-blur-sm" />
      <div className="relative min-h-screen flex items-start justify-center py-8 px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 30 }}
          transition={{ duration: 0.35 }}
          className="relative w-full max-w-2xl rounded-2xl overflow-hidden bg-chef-surface border border-white/10 shadow-cinematic"
          onClick={(e) => e.stopPropagation()}
          data-testid="diary-detail-modal"
        >
          {/* Close */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/50 backdrop-blur-sm hover:bg-black/70 transition-colors"
            data-testid="diary-detail-close"
          >
            <X className="w-5 h-5 text-chef-platinum" strokeWidth={1.5} />
          </button>

          {/* Header */}
          <div className="flex items-start gap-5 p-6 pb-4 border-b border-white/5">
            {posterUrl ? (
              <img src={posterUrl} alt={movie.title} className="w-20 h-[120px] rounded-lg object-cover flex-shrink-0" />
            ) : (
              <div className="w-20 h-[120px] rounded-lg bg-chef-bg flex items-center justify-center flex-shrink-0">
                <Film className="w-6 h-6 text-chef-muted/30" />
              </div>
            )}
            <div className="min-w-0 flex-1 pt-1">
              <h2 className="font-serif text-2xl text-chef-platinum leading-tight" data-testid="diary-detail-title">{movie.title}</h2>
              <p className="text-sm text-chef-muted mt-2">
                {watches.length} watch{watches.length !== 1 ? "es" : ""} logged
              </p>
              {/* Summary: latest rating */}
              {watches.length > 0 && (
                <div className="flex items-center gap-2 mt-2">
                  <Star className="w-3.5 h-3.5 text-chef-gold" fill="#C0B283" />
                  <span className="text-sm text-chef-gold">{watches[0].rating?.toFixed(1)}/10</span>
                  <span className="text-xs text-chef-muted">latest</span>
                </div>
              )}
            </div>
          </div>

          {/* Add Watch Button */}
          <div className="px-6 pt-4">
            {!addingNew ? (
              <button
                onClick={() => setAddingNew(true)}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-chef-teal/10 border border-chef-teal/20 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors w-full justify-center"
                data-testid="add-watch-btn"
              >
                <Plus className="w-4 h-4" /> Log a New Watch
              </button>
            ) : (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-chef-bg/60 border border-chef-teal/20 rounded-lg p-4 mb-2"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-chef-platinum font-medium">New Watch</span>
                  <button onClick={() => setAddingNew(false)} className="text-chef-muted hover:text-chef-platinum"><X className="w-4 h-4" /></button>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1">
                      Rating: <span className="text-chef-gold font-medium">{newRating.toFixed(1)}</span>/10
                    </label>
                    <input type="range" min="0" max="10" step="0.1" value={newRating}
                      onChange={(e) => setNewRating(parseFloat(e.target.value))}
                      className="w-full accent-chef-gold" data-testid="new-watch-rating" />
                  </div>
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1">Date</label>
                    <input type="date" value={newDate}
                      onChange={(e) => setNewDate(e.target.value)}
                      max={new Date().toISOString().split("T")[0]}
                      className="w-full bg-chef-surface/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40 [color-scheme:dark]"
                      data-testid="new-watch-date" />
                  </div>
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1">Comment</label>
                    <textarea value={newComment}
                      onChange={(e) => setNewComment(e.target.value.slice(0, 500))}
                      placeholder="How was this viewing?"
                      rows={2}
                      className="w-full bg-chef-surface/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none focus:border-chef-teal/40 resize-none"
                      data-testid="new-watch-comment" />
                  </div>
                  <button
                    onClick={handleAddWatch}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-chef-teal/10 border border-chef-teal/20 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors disabled:opacity-50"
                    data-testid="confirm-add-watch-btn"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    Save Watch
                  </button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Watches List (descending — latest first) */}
          <div className="px-6 py-4 space-y-3 max-h-[50vh] overflow-y-auto" data-testid="watches-list">
            {watches.length === 0 ? (
              <p className="text-center text-sm text-chef-muted/50 py-8">No watches logged yet</p>
            ) : (
              watches.map((w, idx) => {
                const isEditing = editingId === w.id;
                const label = getWatchLabel(idx, watches.length);
                const isRewatch = label !== "First Watch";

                return (
                  <motion.div
                    key={w.id}
                    layout
                    className="bg-chef-bg/40 border border-white/5 rounded-lg p-4 group"
                    data-testid={`watch-entry-${w.id}`}
                  >
                    {isEditing ? (
                      /* Edit mode */
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-chef-muted uppercase tracking-wider flex items-center gap-1.5">
                            {isRewatch && <RotateCcw className="w-3 h-3" />} {label}
                          </span>
                          <button onClick={() => setEditingId(null)} className="text-chef-muted hover:text-chef-platinum"><X className="w-4 h-4" /></button>
                        </div>
                        <div>
                          <label className="block text-xs text-chef-muted mb-1">
                            Rating: <span className="text-chef-gold">{editRating.toFixed(1)}</span>/10
                          </label>
                          <input type="range" min="0" max="10" step="0.1" value={editRating}
                            onChange={(e) => setEditRating(parseFloat(e.target.value))}
                            className="w-full accent-chef-gold" data-testid={`edit-rating-${w.id}`} />
                        </div>
                        <div>
                          <label className="block text-xs text-chef-muted mb-1">Date</label>
                          <input type="date" value={editDate}
                            onChange={(e) => setEditDate(e.target.value)}
                            max={new Date().toISOString().split("T")[0]}
                            className="w-full bg-chef-surface/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40 [color-scheme:dark]"
                            data-testid={`edit-date-${w.id}`} />
                        </div>
                        <div>
                          <label className="block text-xs text-chef-muted mb-1">Comment</label>
                          <textarea value={editComment}
                            onChange={(e) => setEditComment(e.target.value.slice(0, 500))}
                            rows={2}
                            className="w-full bg-chef-surface/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40 resize-none"
                            data-testid={`edit-comment-${w.id}`} />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveEdit}
                            disabled={saving}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-chef-teal/10 border border-chef-teal/20 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors disabled:opacity-50"
                            data-testid={`save-edit-${w.id}`}
                          >
                            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                            Save
                          </button>
                          <button onClick={() => setEditingId(null)}
                            className="px-4 py-2 rounded-lg text-sm text-chef-muted hover:text-chef-platinum hover:bg-white/5 transition-colors">
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* View mode */
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-chef-muted uppercase tracking-wider flex items-center gap-1.5">
                            {isRewatch && <RotateCcw className="w-3 h-3" />} {label}
                            {w.source === "letterboxd" && (
                              <span className="text-[9px] px-1 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 font-medium ml-1">LB</span>
                            )}
                          </span>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => startEdit(w)}
                              className="p-1.5 rounded-md text-chef-muted/50 hover:text-chef-platinum hover:bg-white/5 transition-colors"
                              data-testid={`edit-watch-${w.id}`}
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDeleteWatch(w.id)}
                              className="p-1.5 rounded-md text-chef-muted/50 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                              data-testid={`delete-watch-${w.id}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1 text-sm text-chef-gold">
                            <Star className="w-3.5 h-3.5" fill="currentColor" />
                            {(w.rating || 0).toFixed(1)}
                          </span>
                          {w.date && (
                            <span className="flex items-center gap-1 text-sm text-chef-muted">
                              <Calendar className="w-3.5 h-3.5" />
                              {w.date}
                            </span>
                          )}
                        </div>
                        {w.comment && (
                          <div className="flex items-start gap-1.5 mt-2">
                            <MessageSquare className="w-3.5 h-3.5 text-chef-muted/50 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-chef-muted leading-relaxed">{w.comment}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </motion.div>
                );
              })
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

// ========== DIARY TAB ==========
const DiaryTab = () => {
  const debounceRef = useRef(null);
  const [watchHistory, setWatchHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [addingMovie, setAddingMovie] = useState(null);
  const [addRating, setAddRating] = useState(7.0);
  const [addDate, setAddDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedMovie, setSelectedMovie] = useState(null);

  useEffect(() => { fetchHistory(); }, []);

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

  return (
    <div>
      <p className="text-sm text-chef-muted mb-6">
        {watchHistory.length} movie{watchHistory.length !== 1 ? "s" : ""} tracked
      </p>

      {/* Search to add */}
      <div className="relative mb-6">
        <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-3">
          <Search className="w-4 h-4 text-chef-muted/40" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search a movie to add to your diary..."
            className="flex-1 bg-transparent text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none"
            data-testid="diary-search-input"
          />
          {searching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
        </div>
        {results.length > 0 && !addingMovie && (
          <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
            {results.map((m) => {
              const inHistory = watchHistory.some((h) => h.tmdb_id === m.id);
              return (
                <button
                  key={m.id}
                  onClick={() => handleSelect(m)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${inHistory ? "opacity-50" : "hover:bg-white/5"}`}
                  data-testid={`diary-result-${m.id}`}
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
                  {inHistory && <span className="text-xs text-chef-teal">In diary</span>}
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
                      type="range" min="0" max="10" step="0.1" value={addRating}
                      onChange={(e) => setAddRating(parseFloat(e.target.value))}
                      className="w-full accent-chef-gold"
                      data-testid="diary-rating-slider"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">Watch Date</label>
                    <input
                      type="date" value={addDate}
                      onChange={(e) => setAddDate(e.target.value)}
                      max={new Date().toISOString().split("T")[0]}
                      className="w-full bg-chef-bg/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40 [color-scheme:dark]"
                      data-testid="diary-date-input"
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={handleAdd}
                    className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-chef-teal/10 border border-chef-teal/20 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
                    data-testid="confirm-add-diary-btn"
                  >
                    <Check className="w-3.5 h-3.5" /> Add to Diary
                  </button>
                  <button
                    onClick={() => setAddingMovie(null)}
                    className="px-4 py-2.5 rounded-lg text-sm text-chef-muted hover:text-chef-platinum hover:bg-white/5 transition-colors"
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
              className="flex items-center gap-4 px-4 py-3 rounded-lg bg-chef-surface/40 border border-white/5 hover:border-white/10 transition-colors group cursor-pointer"
              onClick={() => setSelectedMovie(item)}
              data-testid={`diary-item-${item.tmdb_id}`}
            >
              {item.poster_path ? (
                <img src={`https://image.tmdb.org/t/p/w92${item.poster_path}`} alt="" className="w-10 h-15 rounded object-cover flex-shrink-0" />
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
                  {item.source === "letterboxd" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 uppercase tracking-wider font-medium">LB</span>
                  )}
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleRemove(item.tmdb_id, item.title); }}
                className="p-2 rounded-lg text-chef-muted/30 hover:text-red-400 hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100"
                data-testid={`remove-diary-${item.tmdb_id}`}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Film className="w-10 h-10 text-chef-muted/20 mx-auto mb-3" />
          <p className="text-sm text-chef-muted/50">No movies in your diary yet</p>
          <p className="text-xs text-chef-muted/30 mt-1">Search above to start tracking!</p>
        </div>
      )}

      {/* Diary Detail Modal */}
      <AnimatePresence>
        {selectedMovie && (
          <DiaryDetailModal
            movie={selectedMovie}
            onClose={() => setSelectedMovie(null)}
            onMovieUpdated={(updated) => {
              setWatchHistory((prev) => prev.map((m) => m.tmdb_id === updated.tmdb_id ? updated : m));
              setSelectedMovie(updated);
            }}
            onMovieRemoved={(tmdbId) => {
              setWatchHistory((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// ========== WATCHLIST TAB ==========
const WatchlistTab = () => {
  const debounceRef = useRef(null);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => { fetchWatchlist(); }, []);

  const fetchWatchlist = async () => {
    const token = getToken();
    if (!token) { setLoading(false); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API}/user/watchlist`, { headers: authHeaders() });
      setWatchlist(res.data || []);
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

  const handleAdd = async (movie) => {
    try {
      await axios.post(`${API}/user/watchlist`, {
        tmdb_id: movie.id,
        title: movie.title,
        poster_path: movie.poster_url ? movie.poster_url.split("/").pop() : null,
        release_date: movie.year || null,
        vote_average: movie.rating || null,
      }, { headers: authHeaders() });
      toast.success(`Added "${movie.title}" to watchlist`);
      setQuery("");
      setResults([]);
      fetchWatchlist();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    }
  };

  const handleRemove = async (tmdbId, title) => {
    try {
      await axios.delete(`${API}/user/watchlist/${tmdbId}`, { headers: authHeaders() });
      setWatchlist((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
      toast.success(`Removed "${title}"`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to remove");
    }
  };

  return (
    <div>
      <p className="text-sm text-chef-muted mb-6">
        {watchlist.length} movie{watchlist.length !== 1 ? "s" : ""} to watch
      </p>

      {/* Search to add */}
      <div className="relative mb-6">
        <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-3">
          <Search className="w-4 h-4 text-chef-muted/40" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search a movie to add to your watchlist..."
            className="flex-1 bg-transparent text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none"
            data-testid="watchlist-search-input"
          />
          {searching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
        </div>
        {results.length > 0 && (
          <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
            {results.map((m) => {
              const inList = watchlist.some((w) => w.tmdb_id === m.id);
              return (
                <button
                  key={m.id}
                  onClick={() => !inList && handleAdd(m)}
                  disabled={inList}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${inList ? "opacity-50 cursor-not-allowed" : "hover:bg-white/5"}`}
                  data-testid={`watchlist-result-${m.id}`}
                >
                  {m.poster_url ? (
                    <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                  ) : (
                    <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                    <p className="text-xs text-chef-muted">{m.year}{m.rating ? ` / ${m.rating}` : ""}</p>
                  </div>
                  {inList ? (
                    <span className="text-xs text-chef-teal flex-shrink-0">In watchlist</span>
                  ) : (
                    <Plus className="w-4 h-4 text-chef-muted flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Watchlist items */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-chef-teal animate-spin" />
        </div>
      ) : watchlist.length > 0 ? (
        <div className="space-y-2">
          {watchlist.map((item) => (
            <motion.div
              key={item.tmdb_id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-4 px-4 py-3 rounded-lg bg-chef-surface/40 border border-white/5 hover:border-white/10 transition-colors group"
              data-testid={`watchlist-item-${item.tmdb_id}`}
            >
              {item.poster_path ? (
                <img src={`https://image.tmdb.org/t/p/w92${item.poster_path}`} alt="" className="w-10 h-15 rounded object-cover flex-shrink-0" />
              ) : (
                <div className="w-10 h-15 rounded bg-chef-bg flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-chef-platinum truncate font-medium">{item.title}</p>
                <div className="flex items-center gap-3 mt-1">
                  {item.vote_average && (
                    <span className="flex items-center gap-1 text-xs text-chef-gold">
                      <Star className="w-3 h-3" fill="currentColor" />
                      {item.vote_average.toFixed(1)}
                    </span>
                  )}
                  {item.release_date && (
                    <span className="text-xs text-chef-muted">{item.release_date}</span>
                  )}
                  {item.genres && item.genres.length > 0 && (
                    <span className="text-xs text-chef-muted/60">{item.genres.slice(0, 2).join(", ")}</span>
                  )}
                  {item.source === "letterboxd" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400 uppercase tracking-wider font-medium">LB</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleRemove(item.tmdb_id, item.title)}
                className="p-2 rounded-lg text-chef-muted/30 hover:text-red-400 hover:bg-red-500/10 transition-all opacity-0 group-hover:opacity-100"
                data-testid={`remove-watchlist-${item.tmdb_id}`}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Bookmark className="w-10 h-10 text-chef-muted/20 mx-auto mb-3" />
          <p className="text-sm text-chef-muted/50">Your watchlist is empty</p>
          <p className="text-xs text-chef-muted/30 mt-1">Search above or add movies from any movie detail view!</p>
        </div>
      )}
    </div>
  );
};

// ========== PROFILE TAB ==========
const ProfileTab = ({ user, onUserUpdate }) => {
  const debounceRef = useRef(null);
  const [favoriteMovies, setFavoriteMovies] = useState(user?.favorite_movies || []);
  const [movieQuery, setMovieQuery] = useState("");
  const [movieResults, setMovieResults] = useState([]);
  const [movieSearching, setMovieSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(true);

  useEffect(() => {
    setFavoriteMovies(user?.favorite_movies || []);
  }, [user]);

  useEffect(() => { fetchInsights(); }, []);

  const fetchInsights = async () => {
    setInsightsLoading(true);
    try {
      const res = await axios.get(`${API}/user/profile-insights`, { headers: authHeaders() });
      setInsights(res.data);
    } catch {} finally { setInsightsLoading(false); }
  };

  const handleMovieSearch = useCallback((q) => {
    setMovieQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (q.length < 2) { setMovieResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setMovieSearching(true);
      try {
        const res = await axios.get(`${API}/movies/search-tmdb?query=${encodeURIComponent(q)}`);
        setMovieResults(res.data.results || []);
      } catch { setMovieResults([]); }
      finally { setMovieSearching(false); }
    }, 350);
  }, []);

  const handleAddMovie = (movie) => {
    if (favoriteMovies.length >= 5 || favoriteMovies.some((m) => m.id === movie.id)) return;
    const updated = [...favoriteMovies, movie];
    setFavoriteMovies(updated);
    setMovieQuery("");
    setMovieResults([]);
    saveMovies(updated);
  };

  const handleRemoveMovie = (movieId) => {
    const updated = favoriteMovies.filter((m) => m.id !== movieId);
    setFavoriteMovies(updated);
    saveMovies(updated);
  };

  const saveMovies = async (movies) => {
    setSaving(true);
    try {
      const res = await axios.put(`${API}/auth/profile`, { favorite_movies: movies }, { headers: authHeaders() });
      if (onUserUpdate) onUserUpdate(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  const Section = ({ title, icon: Icon, children, subtitle }) => (
    <div className="mb-8">
      <div className="flex items-center gap-2.5 mb-1">
        <Icon className="w-4 h-4 text-chef-teal" strokeWidth={1.5} />
        <h3 className="font-serif text-lg text-chef-platinum tracking-wide">{title}</h3>
      </div>
      {subtitle && <p className="text-xs text-chef-muted/50 mb-4 ml-6.5">{subtitle}</p>}
      {!subtitle && <div className="mb-4" />}
      {children}
    </div>
  );

  const TMDB_IMG = "https://image.tmdb.org/t/p/";

  const RankedList = ({ items, showImage }) => {
    if (!items || items.length === 0) {
      return <p className="text-sm text-chef-muted/40 ml-1">Not enough watch data yet</p>;
    }
    
    // Helper to format preference as percentage with 2 decimal places
    const formatPreference = (avgPreference, avgExpected) => {
      if (avgPreference === undefined || avgExpected === undefined || avgExpected === 0) return null;
      // Percentage increase = (preference / expected) * 100
      const percentChange = (avgPreference / avgExpected) * 100;
      return Math.abs(percentChange).toFixed(2);
    };

    return (
      <div className="space-y-2">
        {items.map((item, idx) => {
          const percentValue = formatPreference(item.avg_preference, item.avg_expected);
          const isPositive = item.avg_preference !== undefined ? item.avg_preference >= 0 : true;
          
          return (
            <div
              key={item.name}
              className="flex items-center gap-3 px-4 py-3 rounded-lg bg-chef-surface/40 border border-white/5"
              data-testid={`ranked-item-${idx}`}
            >
              <span className="text-lg font-serif text-chef-muted/30 w-6 text-center flex-shrink-0">{idx + 1}</span>
              {showImage && item.profile_path ? (
                <img src={`${TMDB_IMG}w45${item.profile_path}`} alt="" className="w-8 h-8 rounded-full object-cover flex-shrink-0" />
              ) : showImage ? (
                <div className="w-8 h-8 rounded-full bg-chef-bg flex-shrink-0 flex items-center justify-center">
                  <User className="w-3.5 h-3.5 text-chef-muted/30" />
                </div>
              ) : null}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-chef-platinum font-medium truncate">{item.name}</p>
                <p className="text-xs text-chef-muted">
                  {item.count} movie{item.count !== 1 ? "s" : ""}
                  {percentValue !== null && (
                    <span className={`ml-2 inline-flex items-center gap-0.5 ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                      <span className="text-[10px]">{isPositive ? "▲" : "▼"}</span>
                      {percentValue}%
                    </span>
                  )}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div>
      {/* Top 5 Favorite Movies (user-chosen) */}
      <Section title="Top 5 Favorite Movies" icon={Film}>
        {favoriteMovies.length < 5 && (
          <div className="relative mb-4">
            <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-2.5">
              <Search className="w-4 h-4 text-chef-muted/40" />
              <input
                type="text"
                value={movieQuery}
                onChange={(e) => handleMovieSearch(e.target.value)}
                placeholder="Search for a movie..."
                className="flex-1 bg-transparent text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none"
                data-testid="profile-movie-search-input"
              />
              {movieSearching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
            </div>
            {movieResults.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 z-20 bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
                {movieResults.map((m) => {
                  const isAdded = favoriteMovies.some((fm) => fm.id === m.id);
                  return (
                    <button
                      key={m.id}
                      onClick={() => !isAdded && handleAddMovie(m)}
                      disabled={isAdded}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${isAdded ? "opacity-40 cursor-not-allowed" : "hover:bg-white/5"}`}
                      data-testid={`profile-movie-result-${m.id}`}
                    >
                      {m.poster_url ? (
                        <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                      ) : (
                        <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                        <p className="text-xs text-chef-muted">{m.year}{m.rating ? ` / ${m.rating}` : ""}</p>
                      </div>
                      {isAdded && <Check className="w-4 h-4 text-chef-teal ml-auto flex-shrink-0" />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
        <div className="grid grid-cols-5 gap-3">
          {[...Array(5)].map((_, i) => {
            const movie = favoriteMovies[i];
            return (
              <div key={i} className="relative aspect-[2/3] rounded-lg overflow-hidden border border-white/10 bg-chef-surface/40">
                {movie ? (
                  <>
                    {movie.poster_url ? (
                      <img src={movie.poster_url} alt={movie.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Film className="w-6 h-6 text-chef-muted/30" />
                      </div>
                    )}
                    <button
                      onClick={() => handleRemoveMovie(movie.id)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-black/70 text-white hover:bg-red-500/80 transition-colors"
                      data-testid={`profile-remove-movie-${i}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                    <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                      <p className="text-[10px] text-white leading-tight truncate">{movie.title}</p>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-1">
                    <span className="text-xl font-serif text-chef-muted/20">{i + 1}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {saving && (
          <div className="flex items-center gap-2 mt-2 text-xs text-chef-muted">
            <Loader2 className="w-3 h-3 animate-spin" /> Saving...
          </div>
        )}
      </Section>

      {/* Auto-ranked Insights */}
      {insightsLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-chef-teal animate-spin" />
        </div>
      ) : (
        <>
          <Section title="Top Genres" icon={Heart} subtitle="Ranked by your watch history and ratings">
            <RankedList items={insights?.genres} />
          </Section>

          <Section title="Top Actors" icon={Users} subtitle="Based on movies you've watched and rated">
            <RankedList items={insights?.actors} showImage />
          </Section>

          <Section title="Top Directors" icon={Clapperboard} subtitle="Based on movies you've watched and rated">
            <RankedList items={insights?.directors} showImage />
          </Section>
        </>
      )}
    </div>
  );
};

// ========== MAIN PAGE ==========
const MyMoviesPage = ({ user, onUserUpdate }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("diary");

  if (!user) {
    return (
      <main className="pb-24 pt-20 px-4 md:px-8">
        <div className="max-w-3xl mx-auto text-center py-20">
          <Film className="w-12 h-12 text-chef-muted/30 mx-auto mb-4" />
          <h2 className="font-serif text-2xl text-chef-platinum mb-2" data-testid="my-movies-login-prompt">Sign in to view your movies</h2>
          <p className="text-sm text-chef-muted mb-6">Log in to track your diary, build your watchlist, and personalize your profile.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 rounded-full bg-chef-teal/10 border border-chef-teal/20 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
            data-testid="my-movies-go-home-btn"
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
        <h1 className="font-serif text-3xl md:text-4xl tracking-tight text-chef-platinum mb-6" data-testid="my-movies-title">
          My Movies
        </h1>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-8 bg-chef-surface/40 rounded-xl p-1 border border-white/5" data-testid="my-movies-tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200
                  ${isActive
                    ? "bg-chef-surface border border-white/10 text-chef-platinum shadow-sm"
                    : "text-chef-muted hover:text-chef-platinum hover:bg-white/5"
                  }`}
                data-testid={`tab-${tab.id}`}
              >
                <Icon className="w-4 h-4" strokeWidth={1.5} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "diary" && <DiaryTab />}
            {activeTab === "watchlist" && <WatchlistTab />}
            {activeTab === "profile" && <ProfileTab user={user} onUserUpdate={onUserUpdate} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  );
};

export default MyMoviesPage;
