import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Camera, X, Plus, Search, Upload, Check,
  Film, Star, Users, FileText, Loader2, Tv
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GENDER_OPTIONS = [
  { value: "male", label: "M" },
  { value: "female", label: "F" },
  { value: "", label: "Prefer not to say" },
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

  const [gender, setGender] = useState(user?.gender || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [streamingServices, setStreamingServices] = useState(user?.streaming_services || []);
  const [letterboxdData, setLetterboxdData] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [csvUploading, setCsvUploading] = useState(false);

  useEffect(() => {
    setGender(user?.gender || "");
    setBio(user?.bio || "");
    setAvatarUrl(user?.avatar_url || "");
    setStreamingServices(user?.streaming_services || []);
  }, [user]);

  useEffect(() => { fetchLetterboxdData(); }, []);

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

  const handleCsvUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(`${API}/auth/import-letterboxd`, formData, {
        headers: { ...authHeaders(), "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      toast.success(res.data.message);
      if (res.data.stats) {
        setLetterboxdData({
          connected: true,
          stats: res.data.stats,
          imported_at: new Date().toISOString(),
        });
      } else {
        fetchLetterboxdData();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Import failed");
    } finally {
      setCsvUploading(false);
      if (csvInputRef.current) csvInputRef.current.value = "";
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
        { gender, bio, streaming_services: streamingServices },
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
              <div className="flex gap-2" data-testid="gender-select">
                {GENDER_OPTIONS.map((o) => {
                  const isActive = gender === o.value;
                  return (
                    <button
                      key={o.value}
                      type="button"
                      onClick={() => setGender(o.value)}
                      className={`px-5 py-2.5 rounded-lg text-sm font-medium border transition-all duration-200
                        ${isActive
                          ? "bg-chef-teal/15 border-chef-teal/40 text-chef-teal"
                          : "bg-transparent border-white/10 text-chef-muted hover:border-white/20 hover:text-chef-platinum"
                        }`}
                      data-testid={`gender-option-${o.value || "none"}`}
                    >
                      {o.label}
                    </button>
                  );
                })}
              </div>
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
                  {letterboxdData.stats ? (
                    <p className="text-xs text-chef-muted">
                      {letterboxdData.stats.diary_added > 0 && `${letterboxdData.stats.diary_added} diary entries`}
                      {letterboxdData.stats.diary_updated > 0 && ` + ${letterboxdData.stats.diary_updated} updated`}
                      {letterboxdData.stats.watchlist_added > 0 && ` / ${letterboxdData.stats.watchlist_added} watchlist items`}
                      {letterboxdData.stats.skipped > 0 && ` (${letterboxdData.stats.skipped} skipped)`}
                    </p>
                  ) : (
                    <p className="text-xs text-chef-muted">
                      {letterboxdData.total_movies} movies imported
                      {letterboxdData.rated_movies > 0 && ` / ${letterboxdData.rated_movies} rated`}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => csvInputRef.current?.click()}
                className="text-xs text-chef-teal hover:text-chef-teal/80 transition-colors"
                data-testid="reimport-letterboxd-btn"
              >
                Re-import
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
                <>
                  <Loader2 className="w-8 h-8 text-chef-teal animate-spin" />
                  <p className="text-sm text-chef-teal">Importing &mdash; this may take a minute...</p>
                </>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-chef-muted/40" />
                  <div className="text-center">
                    <p className="text-sm text-chef-platinum">Upload your Letterboxd export</p>
                    <p className="text-xs text-chef-muted/50 mt-1">
                      ZIP or CSV &mdash; Go to Letterboxd Settings &gt; Import &amp; Export &gt; Export Your Data
                    </p>
                    <p className="text-xs text-chef-muted/30 mt-0.5">
                      Ratings &amp; reviews go to Diary, watchlist goes to Watchlist
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
          <input
            ref={csvInputRef}
            type="file"
            accept=".csv,.zip"
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
