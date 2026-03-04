import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Camera, X, Plus, Search, Upload, Check,
  Film, Star, Users, FileText, Loader2, Tv, Trash2, Calendar
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GENDER_OPTIONS = [
  { value: "", label: "Prefer not to say" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "non-binary", label: "Non-binary" },
];

const STREAMING_SERVICES = [
  { id: "netflix", name: "Netflix", color: "#E50914" },
  { id: "prime", name: "Prime Video", color: "#00A8E1" },
  { id: "disney", name: "Disney+", color: "#113CCF" },
  { id: "hulu", name: "Hulu", color: "#1CE783" },
  { id: "apple", name: "Apple TV+", color: "#A2AAAD" },
  { id: "hbo", name: "Max", color: "#002BE7" },
  { id: "paramount", name: "Paramount+", color: "#0064FF" },
];

const Section = ({ title, icon: Icon, children }) => (
  <div className="mb-10">
    <div className="flex items-center gap-2.5 mb-5">
      <Icon className="w-4 h-4 text-chef-teal" strokeWidth={1.5} />
      <h2 className="font-serif text-lg text-chef-platinum tracking-wide">{title}</h2>
    </div>
    {children}
  </div>
);

const UserDetails = ({ user, onUserUpdate }) => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const csvInputRef = useRef(null);
  const debounceRef = useRef(null);
  const historyDebounceRef = useRef(null);

  const [gender, setGender] = useState(user?.gender || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [favoriteActors, setFavoriteActors] = useState(user?.favorite_actors || []);
  const [actorInput, setActorInput] = useState("");
  const [favoriteMovies, setFavoriteMovies] = useState(user?.favorite_movies || []);
  const [streamingServices, setStreamingServices] = useState(user?.streaming_services || []);
  const [movieQuery, setMovieQuery] = useState("");
  const [movieResults, setMovieResults] = useState([]);
  const [movieSearching, setMovieSearching] = useState(false);
  const [letterboxdData, setLetterboxdData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [csvUploading, setCsvUploading] = useState(false);

  // Watch history state
  const [watchHistory, setWatchHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyResults, setHistoryResults] = useState([]);
  const [historySearching, setHistorySearching] = useState(false);
  const [addingMovie, setAddingMovie] = useState(null); // movie being added
  const [addRating, setAddRating] = useState(7.0);
  const [addDate, setAddDate] = useState(new Date().toISOString().split("T")[0]);

  // Sync state when user prop changes
  useEffect(() => {
    setGender(user?.gender || "");
    setBio(user?.bio || "");
    setAvatarUrl(user?.avatar_url || "");
    setFavoriteActors(user?.favorite_actors || []);
    setFavoriteMovies(user?.favorite_movies || []);
    setStreamingServices(user?.streaming_services || []);
  }, [user]);

  useEffect(() => {
    fetchLetterboxdData();
    fetchWatchHistory();
  }, []);

  const getToken = () => localStorage.getItem("chef_token");
  const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

  const fetchLetterboxdData = async () => {
    const token = getToken();
    if (!token) return;
    try {
      const res = await axios.get(`${API}/auth/letterboxd-data`, { headers: authHeaders() });
      setLetterboxdData(res.data);
    } catch {}
  };

  const fetchWatchHistory = async () => {
    const token = getToken();
    if (!token) return;
    setHistoryLoading(true);
    try {
      const res = await axios.get(`${API}/user/watch-history`, { headers: authHeaders() });
      setWatchHistory(res.data || []);
    } catch {}
    finally { setHistoryLoading(false); }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/auth/upload-avatar`, formData, {
        headers: { ...authHeaders(), "Content-Type": "multipart/form-data" },
      });
      setAvatarUrl(res.data.avatar_url);
      toast.success("Photo updated");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleAddActor = () => {
    const name = actorInput.trim();
    if (!name || favoriteActors.includes(name) || favoriteActors.length >= 20) return;
    setFavoriteActors((prev) => [...prev, name]);
    setActorInput("");
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
    setFavoriteMovies((prev) => [...prev, movie]);
    setMovieQuery("");
    setMovieResults([]);
  };

  // Watch History: search for movies to add
  const handleHistorySearch = useCallback((q) => {
    setHistoryQuery(q);
    if (historyDebounceRef.current) clearTimeout(historyDebounceRef.current);
    if (q.length < 2) { setHistoryResults([]); return; }
    historyDebounceRef.current = setTimeout(async () => {
      setHistorySearching(true);
      try {
        const res = await axios.get(`${API}/movies/search-tmdb?query=${encodeURIComponent(q)}`);
        setHistoryResults(res.data.results || []);
      } catch { setHistoryResults([]); }
      finally { setHistorySearching(false); }
    }, 350);
  }, []);

  const handleSelectHistoryMovie = (movie) => {
    setAddingMovie(movie);
    setAddRating(7.0);
    setAddDate(new Date().toISOString().split("T")[0]);
    setHistoryQuery("");
    setHistoryResults([]);
  };

  const handleConfirmAddToHistory = async () => {
    if (!addingMovie) return;
    try {
      await axios.post(`${API}/user/watch-history`, {
        tmdb_id: addingMovie.id,
        user_rating: addRating,
        watched_date: addDate,
        title: addingMovie.title,
        poster_path: addingMovie.poster_url ? addingMovie.poster_url.split("/").pop() : null,
      }, { headers: authHeaders() });
      toast.success(`Added "${addingMovie.title}" to history`);
      setAddingMovie(null);
      fetchWatchHistory();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add");
    }
  };

  const handleRemoveFromHistory = async (tmdbId, title) => {
    try {
      await axios.delete(`${API}/user/watch-history/${tmdbId}`, { headers: authHeaders() });
      setWatchHistory((prev) => prev.filter((m) => m.tmdb_id !== tmdbId));
      toast.success(`Removed "${title}" from history`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to remove");
    }
  };

  const handleCsvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/auth/import-letterboxd`, formData, {
        headers: { ...authHeaders(), "Content-Type": "multipart/form-data" },
      });
      toast.success(res.data.message);
      fetchLetterboxdData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Import failed");
    } finally {
      setCsvUploading(false);
    }
  };

  const toggleStreaming = (id) => {
    setStreamingServices((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await axios.put(
        `${API}/auth/profile`,
        { gender, bio, favorite_actors: favoriteActors, favorite_movies: favoriteMovies, streaming_services: streamingServices },
        { headers: authHeaders() }
      );
      if (onUserUpdate) onUserUpdate(res.data);
      toast.success("Details saved");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const avatarSrc = avatarUrl
    ? avatarUrl.startsWith("/api") ? `${process.env.REACT_APP_BACKEND_URL}${avatarUrl}` : avatarUrl
    : null;

  // Auth guard (after all hooks)
  if (!user) {
    return (
      <main className="pb-24 pt-20 px-4 md:px-8">
        <div className="max-w-2xl mx-auto text-center py-20">
          <Users className="w-12 h-12 text-chef-muted/30 mx-auto mb-4" />
          <h2 className="font-serif text-2xl text-chef-platinum mb-2">Sign in to edit your details</h2>
          <p className="text-sm text-chef-muted mb-6">Log in or create an account to personalize your profile.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 rounded-full bg-chef-teal/10 border border-chef-teal/20
                     text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
            data-testid="details-login-redirect"
          >
            Go Home
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="pb-24 pt-20 px-4 md:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-10">
          <button
            onClick={() => navigate("/")}
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            data-testid="details-back-btn"
          >
            <ArrowLeft className="w-5 h-5 text-chef-muted" />
          </button>
          <h1 className="font-serif text-3xl md:text-4xl tracking-tight text-chef-platinum">
            Your Details
          </h1>
        </div>

        {/* Profile Photo */}
        <Section title="Profile Photo" icon={Camera}>
          <div className="flex items-center gap-6">
            <div
              className="relative w-24 h-24 rounded-full border-2 border-white/10
                        flex items-center justify-center overflow-hidden bg-chef-surface
                        cursor-pointer group"
              onClick={() => fileInputRef.current?.click()}
              data-testid="avatar-upload"
            >
              {avatarSrc ? (
                <img src={avatarSrc} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <Users className="w-8 h-8 text-chef-muted/40" />
              )}
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center
                            opacity-0 group-hover:opacity-100 transition-opacity">
                {uploading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Camera className="w-5 h-5 text-white" />
                )}
              </div>
            </div>
            <div>
              <p className="text-sm text-chef-muted">Click to upload a photo</p>
              <p className="text-xs text-chef-muted/50 mt-1">JPG, PNG, or WebP. Max 2MB.</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={handleAvatarUpload}
              data-testid="avatar-file-input"
            />
          </div>
        </Section>

        {/* Personal Info */}
        <Section title="Personal Info" icon={Users}>
          <div className="space-y-5">
            <div>
              <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-3
                         text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40
                         transition-colors appearance-none"
                data-testid="gender-select"
              >
                {GENDER_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value} className="bg-chef-bg">{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                One Liner Bio <span className="text-chef-muted/40">({bio.length}/150)</span>
              </label>
              <input
                type="text"
                value={bio}
                onChange={(e) => setBio(e.target.value.slice(0, 150))}
                placeholder="Cinephile, night owl, Kubrick devotee..."
                className="w-full bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-3
                         text-sm text-chef-platinum placeholder:text-chef-muted/30
                         focus:outline-none focus:border-chef-teal/40 transition-colors"
                data-testid="bio-input"
              />
            </div>
          </div>
        </Section>

        {/* Streaming Services */}
        <Section title="Your Streaming Services" icon={Tv}>
          <p className="text-sm text-chef-muted mb-4">Select services you subscribe to for personalized "Where to Watch" results.</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {STREAMING_SERVICES.map((svc) => {
              const isActive = streamingServices.includes(svc.id);
              return (
                <button
                  key={svc.id}
                  onClick={() => toggleStreaming(svc.id)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-200 text-left
                    ${isActive
                      ? "bg-white/5 border-white/20"
                      : "bg-chef-surface/40 border-white/5 hover:border-white/10"
                    }`}
                  data-testid={`streaming-checkbox-${svc.id}`}
                >
                  <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 border transition-colors
                    ${isActive ? "border-chef-teal bg-chef-teal/20" : "border-white/20"}`}
                  >
                    {isActive && <Check className="w-3 h-3 text-chef-teal" />}
                  </div>
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: svc.color }} />
                    <span className="text-sm text-chef-platinum truncate">{svc.name}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </Section>

        {/* Favorite Actors */}
        <Section title="Favorite Actors" icon={Star}>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={actorInput}
              onChange={(e) => setActorInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddActor()}
              placeholder="Type actor name and press Enter"
              className="flex-1 bg-chef-surface/60 border border-white/10 rounded-lg px-4 py-2.5
                       text-sm text-chef-platinum placeholder:text-chef-muted/30
                       focus:outline-none focus:border-chef-teal/40 transition-colors"
              data-testid="actor-input"
            />
            <button
              onClick={handleAddActor}
              disabled={!actorInput.trim()}
              className="px-4 py-2.5 rounded-lg bg-chef-teal/10 border border-chef-teal/20
                       text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors
                       disabled:opacity-30 disabled:cursor-not-allowed"
              data-testid="add-actor-btn"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            <AnimatePresence>
              {favoriteActors.map((actor) => (
                <motion.span
                  key={actor}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm
                           bg-chef-surface border border-white/10 text-chef-platinum"
                >
                  {actor}
                  <button
                    onClick={() => setFavoriteActors((prev) => prev.filter((a) => a !== actor))}
                    className="text-chef-muted hover:text-red-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </motion.span>
              ))}
            </AnimatePresence>
            {favoriteActors.length === 0 && (
              <p className="text-sm text-chef-muted/40">No favorite actors added yet</p>
            )}
          </div>
        </Section>

        {/* Top 5 Favorite Movies */}
        <Section title="Top 5 Favorite Movies" icon={Film}>
          {favoriteMovies.length < 5 && (
            <div className="relative mb-4">
              <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10
                            rounded-lg px-4 py-2.5">
                <Search className="w-4 h-4 text-chef-muted/40" />
                <input
                  type="text"
                  value={movieQuery}
                  onChange={(e) => handleMovieSearch(e.target.value)}
                  placeholder="Search for a movie..."
                  className="flex-1 bg-transparent text-sm text-chef-platinum
                           placeholder:text-chef-muted/30 focus:outline-none"
                  data-testid="movie-search-input"
                />
                {movieSearching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
              </div>
              {movieResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1 z-20
                              bg-chef-surface/95 backdrop-blur-xl border border-white/10
                              rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
                  {movieResults.map((m) => {
                    const isAdded = favoriteMovies.some((fm) => fm.id === m.id);
                    return (
                      <button
                        key={m.id}
                        onClick={() => !isAdded && handleAddMovie(m)}
                        disabled={isAdded}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left
                                  transition-colors ${isAdded ? "opacity-40 cursor-not-allowed" : "hover:bg-white/5"}`}
                        data-testid={`movie-result-${m.id}`}
                      >
                        {m.poster_url ? (
                          <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                        ) : (
                          <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                        )}
                        <div className="min-w-0">
                          <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                          <p className="text-xs text-chef-muted">{m.year} {m.rating ? `/ ${m.rating}` : ""}</p>
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
                        onClick={() => setFavoriteMovies((prev) => prev.filter((m) => m.id !== movie.id))}
                        className="absolute top-1 right-1 p-1 rounded-full bg-black/70
                                 text-white hover:bg-red-500/80 transition-colors"
                        data-testid={`remove-movie-${i}`}
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
        </Section>

        {/* Watch History */}
        <Section title="Watch History" icon={Calendar}>
          {/* Search to add */}
          <div className="relative mb-4">
            <div className="flex items-center gap-2 bg-chef-surface/60 border border-white/10
                          rounded-lg px-4 py-2.5">
              <Search className="w-4 h-4 text-chef-muted/40" />
              <input
                type="text"
                value={historyQuery}
                onChange={(e) => handleHistorySearch(e.target.value)}
                placeholder="Search a movie to add to your history..."
                className="flex-1 bg-transparent text-sm text-chef-platinum
                         placeholder:text-chef-muted/30 focus:outline-none"
                data-testid="history-search-input"
              />
              {historySearching && <Loader2 className="w-4 h-4 text-chef-teal animate-spin" />}
            </div>
            {historyResults.length > 0 && !addingMovie && (
              <div className="absolute left-0 right-0 top-full mt-1 z-20
                            bg-chef-surface/95 backdrop-blur-xl border border-white/10
                            rounded-lg overflow-hidden shadow-cinematic max-h-72 overflow-y-auto">
                {historyResults.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => handleSelectHistoryMovie(m)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-white/5 transition-colors"
                    data-testid={`history-result-${m.id}`}
                  >
                    {m.poster_url ? (
                      <img src={m.poster_url} alt="" className="w-8 h-12 rounded object-cover flex-shrink-0" />
                    ) : (
                      <div className="w-8 h-12 rounded bg-chef-bg flex-shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm text-chef-platinum truncate">{m.title}</p>
                      <p className="text-xs text-chef-muted">{m.year}</p>
                    </div>
                  </button>
                ))}
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
                className="mb-6 bg-chef-surface/60 border border-chef-teal/20 rounded-lg p-4 overflow-hidden"
              >
                <div className="flex items-start gap-4">
                  {addingMovie.poster_url ? (
                    <img src={addingMovie.poster_url} alt="" className="w-14 h-20 rounded object-cover flex-shrink-0" />
                  ) : (
                    <div className="w-14 h-20 rounded bg-chef-bg flex-shrink-0 flex items-center justify-center">
                      <Film className="w-5 h-5 text-chef-muted/30" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-chef-platinum font-medium truncate">{addingMovie.title}</p>
                    <p className="text-xs text-chef-muted mb-3">{addingMovie.year}</p>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1">
                          Rating: <span className="text-chef-gold font-medium">{addRating.toFixed(1)}</span>/10
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
                        <label className="block text-xs text-chef-muted uppercase tracking-wider mb-1">Watch Date</label>
                        <input
                          type="date"
                          value={addDate}
                          onChange={(e) => setAddDate(e.target.value)}
                          max={new Date().toISOString().split("T")[0]}
                          className="w-full bg-chef-bg/80 border border-white/10 rounded-lg px-3 py-2
                                   text-sm text-chef-platinum focus:outline-none focus:border-chef-teal/40"
                          data-testid="history-date-input"
                        />
                      </div>
                    </div>

                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={handleConfirmAddToHistory}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-chef-teal/10 border border-chef-teal/20
                                 text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
                        data-testid="confirm-add-history-btn"
                      >
                        <Check className="w-3.5 h-3.5" /> Add
                      </button>
                      <button
                        onClick={() => setAddingMovie(null)}
                        className="px-4 py-2 rounded-lg text-sm text-chef-muted hover:text-chef-platinum
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
          {historyLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 text-chef-teal animate-spin" />
            </div>
          ) : watchHistory.length > 0 ? (
            <div className="space-y-2">
              {watchHistory.map((item) => (
                <div
                  key={item.tmdb_id}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-chef-surface/40
                           border border-white/5 hover:border-white/10 transition-colors group"
                  data-testid={`history-item-${item.tmdb_id}`}
                >
                  {item.poster_path ? (
                    <img
                      src={`https://image.tmdb.org/t/p/w92${item.poster_path}`}
                      alt=""
                      className="w-9 h-14 rounded object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-9 h-14 rounded bg-chef-bg flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-chef-platinum truncate">{item.title}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-xs text-chef-gold">{(item.user_rating || 0).toFixed(1)}/10</span>
                      {item.last_watched_date && (
                        <span className="text-xs text-chef-muted">{item.last_watched_date}</span>
                      )}
                      {item.watch_count > 1 && (
                        <span className="text-xs text-chef-muted/60">{item.watch_count}x watched</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveFromHistory(item.tmdb_id, item.title)}
                    className="p-2 rounded-lg text-chef-muted/40 hover:text-red-400
                             hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                    data-testid={`remove-history-${item.tmdb_id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-chef-muted/40 text-center py-6">
              No movies in your watch history yet. Search above to start adding!
            </p>
          )}
        </Section>

        {/* Connect Letterboxd */}
        <Section title="Connect Letterboxd" icon={FileText}>
          {letterboxdData?.connected ? (
            <div className="bg-chef-surface/60 border border-chef-teal/20 rounded-lg p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-chef-teal/20 flex items-center justify-center">
                  <Check className="w-4 h-4 text-chef-teal" />
                </div>
                <div>
                  <p className="text-sm text-chef-platinum font-medium">Letterboxd Connected</p>
                  <p className="text-xs text-chef-muted">
                    {letterboxdData.total_movies} movies imported
                    {letterboxdData.rated_movies > 0 && ` / ${letterboxdData.rated_movies} rated`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => csvInputRef.current?.click()}
                className="text-xs text-chef-teal hover:text-chef-teal/80 transition-colors"
                data-testid="reimport-letterboxd-btn"
              >
                Re-import CSV
              </button>
            </div>
          ) : (
            <div
              onClick={() => csvInputRef.current?.click()}
              className="border-2 border-dashed border-white/10 rounded-lg p-8
                       flex flex-col items-center justify-center gap-3
                       hover:border-chef-teal/30 hover:bg-chef-teal/5
                       transition-all cursor-pointer"
              data-testid="letterboxd-dropzone"
            >
              {csvUploading ? (
                <Loader2 className="w-8 h-8 text-chef-teal animate-spin" />
              ) : (
                <Upload className="w-8 h-8 text-chef-muted/40" />
              )}
              <div className="text-center">
                <p className="text-sm text-chef-platinum">
                  {csvUploading ? "Importing..." : "Upload your Letterboxd CSV"}
                </p>
                <p className="text-xs text-chef-muted/50 mt-1">
                  Export from Letterboxd Settings &gt; Import & Export &gt; Export Your Data
                </p>
              </div>
            </div>
          )}
          <input
            ref={csvInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleCsvUpload}
            data-testid="letterboxd-file-input"
          />
        </Section>

        {/* Save Button */}
        <div className="sticky bottom-24 z-10 flex justify-end">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-8 py-3 rounded-full
                     bg-chef-teal/20 border border-chef-teal/30
                     text-chef-teal font-medium text-sm
                     hover:bg-chef-teal/30 transition-colors
                     disabled:opacity-50 shadow-lg shadow-black/30"
            data-testid="save-details-btn"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Save Details
          </motion.button>
        </div>
      </div>
    </main>
  );
};

export default UserDetails;
