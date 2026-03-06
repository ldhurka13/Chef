import React, { useState } from "react";
import { motion } from "framer-motion";

const MovieCard = ({ movie, onClick, index }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  // Calculate varying heights for masonry effect
  const heights = [320, 360, 400, 340, 380, 350, 390, 330];
  const height = heights[index % heights.length];

  return (
    <motion.div
      className="relative overflow-hidden rounded-2xl cursor-pointer group"
      style={{ height }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      data-testid={`movie-card-${movie.id}`}
    >
      {/* Background Image */}
      <div className="absolute inset-0">
        {!imageLoaded && (
          <div className="absolute inset-0 skeleton" />
        )}
        {movie.poster_url ? (
          <img
            src={movie.poster_url}
            alt={movie.title}
            className={`w-full h-full object-cover transition-transform duration-700 
                       ${isHovered ? 'scale-110' : 'scale-100'}
                       ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setImageLoaded(true)}
          />
        ) : (
          <div className="w-full h-full bg-chef-surface flex items-center justify-center">
            <span className="text-chef-muted text-sm">No Image</span>
          </div>
        )}
      </div>

      {/* Gradient Overlay */}
      <div 
        className={`absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent
                    transition-opacity duration-300 ${isHovered ? 'opacity-100' : 'opacity-70'}`}
      />

      {/* Glow Effect on Hover */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{
          boxShadow: isHovered 
            ? 'inset 0 0 60px -10px rgba(45, 212, 191, 0.15)' 
            : 'inset 0 0 0 0 rgba(45, 212, 191, 0)',
        }}
        transition={{ duration: 0.4 }}
      />

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-4">
        {/* Match Percentage and Watchlist Badges - Side by Side */}
        {(movie.match_percentage || movie.curated_score || movie.in_watchlist) && (
          <div className="mb-2 flex items-center gap-2 flex-wrap">
            {(movie.match_percentage || movie.curated_score) && (
              <span className="inline-block px-2 py-1 rounded-full bg-chef-teal/20 
                             text-chef-teal font-sans text-sm font-medium
                             border border-chef-teal/30">
                {movie.curated_score ? `${Math.min(100, Math.round(movie.curated_score))}%` : `${movie.match_percentage}%`} Match
              </span>
            )}
            {movie.in_watchlist && (
              <span className="inline-block px-2 py-1 rounded-full bg-amber-500/20 
                             text-amber-400 font-sans text-xs font-medium
                             border border-amber-500/30">
                Watchlist
              </span>
            )}
          </div>
        )}

        {/* Title */}
        <h3 className="font-serif text-lg md:text-xl leading-tight line-clamp-2 mb-1">
          {movie.title}
        </h3>

        {/* Match Reason or Vibe Tag */}
        <p className="text-chef-gold text-sm italic mt-1 line-clamp-1">
          {movie.match_reason || movie.vibe_tag || "Worth discovering"}
        </p>

        {/* Genres - Shows on Hover */}
        {movie.genres && movie.genres.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: isHovered ? 1 : 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="flex flex-wrap gap-1 mt-2"
          >
            {movie.genres.slice(0, 2).map((genre, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 text-xs text-chef-muted bg-white/10 
                           rounded-full backdrop-blur-sm"
              >
                {genre}
              </span>
            ))}
          </motion.div>
        )}
      </div>

      {/* Border Glow */}
      <div 
        className={`absolute inset-0 rounded-2xl border transition-all duration-300
                    ${isHovered 
                      ? 'border-chef-teal/30 shadow-glow-teal' 
                      : 'border-white/5'}`}
      />
    </motion.div>
  );
};

export default MovieCard;
