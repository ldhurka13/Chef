import React from "react";
import { motion } from "framer-motion";
import { Star, Trash2 } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SafetyNet = ({ movies, onMovieClick, onRefresh }) => {
  const handleRemove = async (e, tmdbId) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API}/user/watch-history/${tmdbId}`);
      toast.success("Removed from watch history");
      if (onRefresh) onRefresh();
      else window.location.reload();
    } catch (error) {
      console.error("Failed to remove:", error);
      toast.error("Failed to remove from history");
    }
  };

  if (!movies || movies.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-flick-muted text-lg mb-4">
          Your watch history is empty
        </p>
        <p className="text-flick-muted/60 text-sm max-w-md">
          Start adding movies to build your personal collection and unlock the "I Can't Even" comfort feature!
        </p>
      </div>
    );
  }

  return (
    <div className="sepia-tone" data-testid="safety-net-section">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
        {movies.map((movie, index) => (
          <motion.div
            key={movie.id || movie.tmdb_id || index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="group relative cursor-pointer"
            onClick={() => onMovieClick({ 
              id: movie.tmdb_id, 
              ...movie 
            })}
            data-testid={`history-movie-${movie.tmdb_id}`}
          >
            {/* Poster */}
            <div className="aspect-[2/3] rounded-xl overflow-hidden bg-flick-surface mb-3
                          ring-1 ring-white/5 group-hover:ring-flick-gold/30
                          transition-all duration-300">
              {movie.poster_path ? (
                <img
                  src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                  alt={movie.title}
                  className="w-full h-full object-cover 
                           group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="text-flick-muted text-xs">No Image</span>
                </div>
              )}
              
              {/* Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent
                            opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>

            {/* Info */}
            <h3 className="font-serif text-sm leading-tight truncate mb-1">
              {movie.title}
            </h3>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                <Star className="w-3 h-3 text-flick-gold" fill="#C0B283" />
                <span className="text-xs text-flick-gold">{movie.user_rating}/10</span>
              </div>
              
              <span className="text-xs text-flick-muted">
                {movie.watch_count > 1 ? `${movie.watch_count}x` : 'Once'}
              </span>
            </div>

            {/* Remove Button */}
            <button
              onClick={(e) => handleRemove(e, movie.tmdb_id)}
              className="absolute top-2 right-2 p-2 rounded-full
                       bg-black/50 backdrop-blur-sm opacity-0 group-hover:opacity-100
                       hover:bg-red-500/30 transition-all duration-200"
              data-testid={`remove-history-${movie.tmdb_id}`}
            >
              <Trash2 className="w-3 h-3 text-white" strokeWidth={1.5} />
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default SafetyNet;
