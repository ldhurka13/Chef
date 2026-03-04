import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Camera, X, Plus, Search, Upload, Check,
  Film, Star, Users, FileText, Loader2
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

  const [gender, setGender] = useState(user?.gender || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [favoriteActors, setFavoriteActors] = useState(user?.favorite_actors || []);
  const [actorInput, setActorInput] = useState("");
  const [favoriteMovies, setFavoriteMovies] = useState(user?.favorite_movies || []);
  const [movieQuery, setMovieQuery] = useState("");
  const [movieResults, setMovieResults] = useState([]);
  const [movieSearching, setMovieSearching] = useState(false);
  const [letterboxdData, setLetterboxdData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [csvUploading, setCsvUploading] = useState(false);

  // Sync state when user prop changes (e.g., after save or re-login)
  useEffect(() => {
    setGender(user?.gender || "");
    setBio(user?.bio || "");
    setAvatarUrl(user?.avatar_url || "");
    setFavoriteActors(user?.favorite_actors || []);
    setFavoriteMovies(user?.favorite_movies || []);
  }, [user]);

  useEffect(() => {
    fetchLetterboxdData();
  }, []);

  const fetchLetterboxdData = async () => {
    const token = localStorage.getItem("chef_token");
    if (!token) return;
    try {
      const res = await axios.get(`${API}/auth/letterboxd-data`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLetterboxdData(res.data);
    } catch {}
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const token = localStorage.getItem("chef_token");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/auth/upload-avatar`, formData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
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

  const debounceRef = useRef(null);
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

  const handleCsvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvUploading(true);
    const token = localStorage.getItem("chef_token");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/auth/import-letterboxd`, formData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
      });
      toast.success(res.data.message);
      fetchLetterboxdData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Import failed");
    } finally {
      setCsvUploading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    const token = localStorage.getItem("chef_token");
    try {
      const res = await axios.put(
        `${API}/auth/profile`,
        { gender, bio, favorite_actors: favoriteActors, favorite_movies: favoriteMovies },
        { headers: { Authorization: `Bearer ${token}` } }
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
