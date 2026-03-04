import React, { useState } from "react";
import { motion } from "framer-motion";
import { Film, Star, Calendar } from "lucide-react";

const CollectionCard = ({ collection, onClick, index }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="relative overflow-hidden rounded-lg cursor-pointer group"
      style={{ height: 420 }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      data-testid={`collection-card-${collection.id}`}
    >
      {/* Background Image */}
      <div className="absolute inset-0">
        {!imageLoaded && (
          <div className="absolute inset-0 skeleton" />
        )}
        {collection.backdrop_url || collection.poster_url ? (
          <img
            src={collection.backdrop_url || collection.poster_url}
            alt={collection.name}
            className={`w-full h-full object-cover transition-transform duration-700 
                       ${isHovered ? 'scale-110' : 'scale-100'}
                       ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setImageLoaded(true)}
          />
        ) : (
          <div className="w-full h-full bg-flick-surface flex items-center justify-center">
            <Film className="w-12 h-12 text-flick-muted" />
          </div>
        )}
      </div>

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />

      {/* Movie Count Badge */}
      <div className="absolute top-3 left-3 px-3 py-1.5 bg-flick-orange/20 border border-flick-orange/40 
                    text-flick-orange text-xs font-medium flex items-center gap-1.5">
        <Film className="w-3 h-3" />
        {collection.movie_count} Films
      </div>

      {/* Rating Badge */}
      {collection.avg_rating > 0 && (
        <div className="absolute top-3 right-3 px-2 py-1 bg-flick-teal/20 border border-flick-teal/30 
                      text-flick-teal text-xs flex items-center gap-1">
          <Star className="w-3 h-3" fill="currentColor" />
          {collection.avg_rating}
        </div>
      )}

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-5">
        {/* Collection Name */}
        <h3 className="font-serif text-xl md:text-2xl leading-tight mb-2">
          {collection.name}
        </h3>

        {/* Year Span */}
        {collection.year_span && (
          <div className="flex items-center gap-1.5 text-flick-muted text-sm mb-3">
            <Calendar className="w-3.5 h-3.5" />
            {collection.year_span}
          </div>
        )}

        {/* Vibe Tag */}
        <p className="text-flick-orange text-sm font-medium mb-3">
          {collection.vibe_tag}
        </p>

        {/* Mini Posters Row - Shows on Hover */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ 
            opacity: isHovered ? 1 : 0, 
            y: isHovered ? 0 : 10 
          }}
          transition={{ duration: 0.3 }}
          className="flex gap-2 mt-3"
        >
          {collection.parts?.slice(0, 5).map((part, idx) => (
            <div 
              key={part.id || idx}
              className="w-10 h-14 rounded overflow-hidden border border-white/10"
            >
              {part.poster_url ? (
                <img 
                  src={part.poster_url} 
                  alt={part.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-flick-surface" />
              )}
            </div>
          ))}
          {collection.parts?.length > 5 && (
            <div className="w-10 h-14 rounded bg-flick-surface/50 border border-white/10 
                          flex items-center justify-center text-xs text-flick-muted">
              +{collection.parts.length - 5}
            </div>
          )}
        </motion.div>
      </div>

      {/* Border Glow */}
      <div 
        className={`absolute inset-0 rounded-lg border transition-all duration-300
                    ${isHovered 
                      ? 'border-flick-orange/40 shadow-glow-orange' 
                      : 'border-white/5'}`}
      />
    </motion.div>
  );
};

export default CollectionCard;
