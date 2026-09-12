import React, { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Plus, Check, X, Film, Loader2, MessageSquare } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "./ui/dialog";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem("chef_token")}` });

const AddToLibraryDialog = ({ open, onOpenChange, mode, existingIds = [], onAdded }) => {
  const debounceRef = useRef(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState(null); // diary mode only
  const [rating, setRating] = useState(7.0);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const existingSet = new Set(existingIds);
  const isDiary = mode === "diary";
  const label = isDiary ? "Diary" : "Watchlist";

  useEffect(() => {
    if (!open) {
      // Reset all state when closing
      setQuery("");
      setResults([]);
      setSelected(null);
      setRating(7.0);
      setDate(new Date().toISOString().split("T")[0]);
      setComment("");
      setSubmitting(false);
    }
  }, [open]);

  const handleSearch = useCallback((q) => {
    setQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (q.length < 2) { setResults([]); return; }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await axios.get(`${API}/movies/search-tmdb?query=${encodeURIComponent(q)}`);
        setResults(res.data.results || []);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 350);
  }, []);

  const extractPosterPath = (movie) =>
    movie.poster_path ||
    (movie.poster_url
      ? movie.poster_url.replace("https://image.tmdb.org/t/p/w185", "").replace("https://image.tmdb.org/t/p/w500", "")
      : null);

  const handlePickWatchlist = async (movie) => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/user/watchlist`, {
        tmdb_id: movie.id,
        title: movie.title,
        poster_path: extractPosterPath(movie),
        release_date: movie.year || null,
        vote_average: movie.rating || null,
      }, { headers: authHeaders() });
      toast.success(`Added "${movie.title}" to watchlist`);
      onAdded && onAdded(movie);
      onOpenChange(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePickDiary = (movie) => {
    setSelected(movie);
    setRating(7.0);
    setDate(new Date().toISOString().split("T")[0]);
    setComment("");
  };

  const handleAddDiary = async () => {
    if (!selected || submitting) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/user/watch-history`, {
        tmdb_id: selected.id,
        user_rating: rating,
        watched_date: date,
        title: selected.title,
        poster_path: extractPosterPath(selected),
        comment,
      }, { headers: authHeaders() });
      toast.success(`Added "${selected.title}"`);
      onAdded && onAdded(selected);
      onOpenChange(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!submitting) onOpenChange(v); }}>
      <DialogContent
        className="max-w-lg bg-chef-surface/95 backdrop-blur-xl border border-white/10 text-chef-platinum shadow-cinematic"
        data-testid={`add-to-${mode}-dialog`}
      >
        <DialogHeader className="text-left">
          <DialogTitle className="font-serif text-2xl tracking-tight text-chef-platinum">
            Add to {label}
          </DialogTitle>
          <DialogDescription className="text-sm text-chef-muted">
            {isDiary
              ? "Search a movie and log your rating, watch date, and thoughts."
              : "Search a movie to save for later."}
          </DialogDescription>
        </DialogHeader>

        {!selected && (
          <div className="flex items-center gap-2 bg-chef-bg/60 border border-white/10 rounded-lg px-3 py-2.5">
            <Search className="w-4 h-4 text-chef-muted/50" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search TMDB…"
              autoFocus
              className="flex-1 bg-transparent text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none"
              data-testid={`add-${mode}-search-input`}
            />
            {searching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
          </div>
        )}

        {/* Results (both modes) */}
        {!selected && results.length > 0 && (
          <div className="max-h-72 overflow-y-auto border border-white/10 rounded-lg divide-y divide-white/5">
            {results.map((m) => {
              const already = existingSet.has(m.id);
              return (
                <button
                  key={m.id}
                  disabled={already || submitting}
                  onClick={() => isDiary ? handlePickDiary(m) : handlePickWatchlist(m)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors
                    ${already ? "opacity-50 cursor-not-allowed" : "hover:bg-white/5"}`}
                  data-testid={`add-${mode}-result-${m.id}`}
                >
                  {m.poster_url ? (
                    <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                  ) : (
                    <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                    <p className="text-xs text-chef-muted">{m.year}{m.rating ? ` · ${m.rating}` : ""}</p>
                  </div>
                  {already ? (
                    <span className="text-xs text-chef-teal flex-shrink-0">In {label.toLowerCase()}</span>
                  ) : isDiary ? (
                    <Check className="w-4 h-4 text-chef-muted flex-shrink-0" />
                  ) : (
                    <Plus className="w-4 h-4 text-chef-muted flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        )}

        {!selected && query.length >= 2 && !searching && results.length === 0 && (
          <p className="text-sm text-chef-muted/60 text-center py-4">No matches on TMDB.</p>
        )}

        {/* Diary rating form */}
        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              className="bg-chef-bg/60 border border-chef-teal/20 rounded-lg p-4"
            >
              <div className="flex items-start gap-3 mb-4">
                {selected.poster_url ? (
                  <img src={selected.poster_url} alt="" className="w-14 h-20 rounded object-cover flex-shrink-0" />
                ) : (
                  <div className="w-14 h-20 rounded bg-chef-bg flex-shrink-0 flex items-center justify-center">
                    <Film className="w-5 h-5 text-chef-muted/30" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-base text-chef-platinum font-medium truncate">{selected.title}</p>
                  <p className="text-xs text-chef-muted">{selected.year}</p>
                </div>
                <button
                  onClick={() => setSelected(null)}
                  className="p-1 rounded hover:bg-white/10 text-chef-muted hover:text-chef-platinum"
                  aria-label="Pick a different movie"
                  data-testid="add-diary-change-movie"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">
                    Your Rating: <span className="text-chef-gold font-medium text-sm">{rating.toFixed(1)}</span>/10
                  </label>
                  <input
                    type="range" min="0" max="10" step="0.1" value={rating}
                    onChange={(e) => setRating(parseFloat(e.target.value))}
                    className="w-full accent-chef-gold"
                    data-testid="add-diary-rating"
                  />
                </div>
                <div>
                  <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">Watch Date</label>
                  <input
                    type="date" value={date}
                    onChange={(e) => setDate(e.target.value)}
                    max={new Date().toISOString().split("T")[0]}
                    className="w-full bg-chef-bg/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40 [color-scheme:dark]"
                    data-testid="add-diary-date"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1.5">
                  <MessageSquare className="w-3 h-3 inline mr-1" />
                  Comment (optional)
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add a note about this watch..."
                  rows={2}
                  className="w-full bg-chef-bg/80 border border-white/10 rounded-lg px-3 py-2 text-sm text-chef-platinum placeholder:text-chef-muted/30 focus:outline-none focus:border-chef-teal/40 resize-none"
                  data-testid="add-diary-comment"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
            className="px-4 py-2 rounded-full text-sm text-chef-muted hover:text-chef-platinum hover:bg-white/5 transition-colors disabled:opacity-50"
            data-testid={`add-${mode}-cancel-btn`}
          >
            Cancel
          </button>
          {selected && isDiary && (
            <button
              type="button"
              onClick={handleAddDiary}
              disabled={submitting}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-full text-sm font-medium
                       bg-chef-teal/20 border border-chef-teal/40 text-chef-teal
                       hover:bg-chef-teal/30 disabled:opacity-50 transition-colors
                       focus:outline-none focus:ring-2 focus:ring-chef-teal/40"
              data-testid="add-diary-confirm-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Add to Diary
            </button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AddToLibraryDialog;
