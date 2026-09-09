/**
 * PersonDetail.js
 * 
 * Modal component displaying person details (actor/director) with their credits.
 * Shows acting and directing credits separately with movie cards.
 */
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { 
  X, User, Film, Clapperboard, Loader2, AlertCircle, 
  ChevronLeft, ChevronRight, Calendar, MapPin
} from "lucide-react";
import MovieCard from "./MovieCard";

const API = process.env.REACT_APP_BACKEND_URL;

// Helper to get auth headers
const authHeaders = () => {
  const token = localStorage.getItem("chef_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const PersonDetail = ({ personId, onClose, onMovieSelect }) => {
  const [person, setPerson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const modalRef = useRef(null);
  
  // Fetch person details and credits
  useEffect(() => {
    if (!personId) return;
    
    const fetchPerson = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const res = await axios.get(`${API}/api/search/person/${personId}`, {
          headers: authHeaders()
        });
        setPerson(res.data);
      } catch (err) {
        console.error("Failed to fetch person:", err);
        setError("Failed to load person details. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchPerson();
  }, [personId]);
  
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [onClose]);
  
  // Handle movie card click
  const handleMovieClick = (credit) => {
    if (onMovieSelect) {
      onMovieSelect({
        id: credit.id,
        media_type: credit.media_type || "movie",
        title: credit.title,
        poster_path: credit.poster_path,
        poster_url: credit.poster_url,
      });
    }
  };
  
  // Credit section component
  const CreditSection = ({ title, icon: Icon, credits }) => {
    const [showAll, setShowAll] = useState(false);
    const displayCredits = showAll ? credits : credits.slice(0, 12);
    
    if (!credits || credits.length === 0) return null;
    
    return (
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="flex items-center gap-2 text-lg font-medium text-chef-platinum">
            <Icon className="w-5 h-5 text-chef-muted" />
            {title}
            <span className="text-sm text-chef-muted font-normal">({credits.length})</span>
          </h3>
          {credits.length > 12 && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-sm text-chef-teal hover:text-chef-teal/80 transition-colors"
            >
              {showAll ? "Show less" : `Show all ${credits.length}`}
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {displayCredits.map((credit, idx) => (
            <div
              key={`${credit.id}-${credit.media_type}-${idx}`}
              data-testid={`person-credit-${credit.media_type}-${credit.id}`}
              className="cursor-pointer group"
              onClick={() => handleMovieClick(credit)}
            >
              <div className="aspect-[2/3] rounded-lg overflow-hidden bg-chef-surface/40 border border-white/10 group-hover:border-white/30 transition-all">
                {credit.poster_url || credit.poster_path ? (
                  <img
                    src={credit.poster_url || `https://image.tmdb.org/t/p/w185${credit.poster_path}`}
                    alt={credit.title}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Film className="w-8 h-8 text-chef-muted/30" />
                  </div>
                )}
              </div>
              <div className="mt-2">
                <p className="text-xs text-chef-platinum line-clamp-1 group-hover:text-white transition-colors">
                  {credit.title}
                </p>
                <p className="text-[10px] text-chef-muted">
                  {credit.year || "—"}
                  {credit.character && (
                    <span className="ml-1">• {credit.character}</span>
                  )}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm"
        onClick={onClose}
        data-testid="person-detail-backdrop"
      >
        <motion.div
          ref={modalRef}
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden bg-chef-bg border border-white/10 rounded-2xl shadow-cinematic"
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby="person-name"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/50 text-white/70 hover:text-white hover:bg-black/70 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
          
          {/* Content */}
          <div className="overflow-y-auto max-h-[90vh]">
            {loading ? (
              // Loading state
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-chef-teal animate-spin" />
              </div>
            ) : error ? (
              // Error state
              <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
                <AlertCircle className="w-10 h-10 text-red-400/60 mb-3" />
                <p className="text-chef-muted mb-4">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 rounded-lg bg-chef-surface text-chef-platinum text-sm hover:bg-white/10 transition-colors"
                >
                  Try again
                </button>
              </div>
            ) : person ? (
              <>
                {/* Person header */}
                <div className="relative">
                  {/* Background gradient */}
                  <div className="absolute inset-0 bg-gradient-to-b from-chef-surface/50 to-chef-bg" />
                  
                  <div className="relative p-6 sm:p-8 flex flex-col sm:flex-row gap-6">
                    {/* Profile image */}
                    <div className="flex-shrink-0 mx-auto sm:mx-0">
                      <div className="w-32 h-32 sm:w-40 sm:h-40 rounded-xl overflow-hidden bg-chef-surface/60 border border-white/10">
                        {person.profile_url || person.profile_path ? (
                          <img
                            src={person.profile_url || `https://image.tmdb.org/t/p/w500${person.profile_path}`}
                            alt={person.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <User className="w-16 h-16 text-chef-muted/30" />
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Person info */}
                    <div className="flex-1 text-center sm:text-left">
                      <h1 
                        id="person-name"
                        className="text-2xl sm:text-3xl font-serif text-chef-platinum mb-2"
                      >
                        {person.name}
                      </h1>
                      
                      {person.known_for_department && (
                        <p className="text-chef-teal text-sm mb-3">
                          {person.known_for_department}
                        </p>
                      )}
                      
                      {/* Meta info */}
                      <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-sm text-chef-muted mb-4">
                        {person.birthday && (
                          <span className="flex items-center gap-1.5">
                            <Calendar className="w-4 h-4" />
                            {person.birthday}
                          </span>
                        )}
                        {person.place_of_birth && (
                          <span className="flex items-center gap-1.5">
                            <MapPin className="w-4 h-4" />
                            {person.place_of_birth}
                          </span>
                        )}
                      </div>
                      
                      {/* Biography */}
                      {person.biography && (
                        <p className="text-sm text-chef-muted/80 line-clamp-4 leading-relaxed">
                          {person.biography}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Credits sections */}
                <div className="px-6 sm:px-8 pb-8">
                  {/* Acting credits */}
                  <CreditSection
                    title="Acting"
                    icon={Film}
                    credits={person.acting}
                  />
                  
                  {/* Directing credits */}
                  <CreditSection
                    title="Directed by"
                    icon={Clapperboard}
                    credits={person.directing}
                  />
                  
                  {/* No credits message */}
                  {(!person.acting || person.acting.length === 0) && 
                   (!person.directing || person.directing.length === 0) && (
                    <div className="text-center py-8">
                      <Film className="w-10 h-10 text-chef-muted/30 mx-auto mb-3" />
                      <p className="text-chef-muted">No credits found</p>
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default PersonDetail;
