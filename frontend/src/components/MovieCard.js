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
          <div className="w-full h-full bg-flick-surface flex items-center justify-center">
            <span className="text-flick-muted text-sm">No Image</span>
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
        {/* Match Percentage */}
        {movie.match_percentage && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: isHovered ? 1 : 0.8, y: 0 }}
            className="mb-2"
          >
            <span className="text-flick-teal font-sans text-sm font-medium">
              {movie.match_percentage}% Match
            </span>
          </motion.div>
        )}

        {/* Title */}
        <h3 className="font-serif text-lg md:text-xl leading-tight line-clamp-2 mb-1">
          {movie.title}
        </h3>

        {/* Vibe Tag - Shows on Hover */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ 
            opacity: isHovered ? 1 : 0, 
            y: isHovered ? 0 : 10 
          }}
          transition={{ duration: 0.3 }}
          className="text-flick-gold text-sm italic mt-2"
        >
          {movie.vibe_tag || "Worth discovering"}
        </motion.p>

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
                className="px-2 py-0.5 text-xs text-flick-muted bg-white/10 
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
                      ? 'border-flick-teal/30 shadow-glow-teal' 
                      : 'border-white/5'}`}
      />
    </motion.div>
  );
};

export default MovieCard;
