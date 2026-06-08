import React from "react";
import { motion } from "framer-motion";

const HeroSection = ({ movie, loading, onMovieClick }) => {
  if (loading) {
    return (
      <section className="relative min-h-[70vh] w-full overflow-hidden">
        <div className="absolute inset-0 skeleton" />
        <div className="absolute inset-0 bg-gradient-to-t from-chef-bg via-chef-bg/50 to-transparent" />
      </section>
    );
  }

  if (!movie) {
    return (
      <section className="relative min-h-[70vh] w-full flex items-center justify-center">
        <p className="text-chef-muted">No featured movie available</p>
      </section>
    );
  }

  return (
    <section 
      className="relative min-h-[70vh] w-full overflow-hidden cursor-pointer"
      data-testid="hero-section"
      onClick={() => onMovieClick(movie)}
    >
      {/* Background Image */}
      <motion.div
        initial={{ scale: 1.1, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        className="absolute inset-0"
      >
        {movie.backdrop_url ? (
          <img
            src={movie.backdrop_url}
            alt={movie.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-chef-surface" />
        )}
      </motion.div>

      {/* Gradient Overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-chef-bg via-chef-bg/60 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-chef-bg/80 via-transparent to-transparent" />

      {/* Vignette */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(circle at center, transparent 0%, #0A0A0B 100%)",
          opacity: 0.4,
        }}
      />

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-8 md:p-16 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <p className="text-sm tracking-[0.3em] uppercase text-chef-gold mb-4">
            Vibe of the Day
          </p>
          
          <h1 className="font-serif text-4xl md:text-6xl lg:text-7xl font-light tracking-tight leading-none mb-6">
            {movie.title}
          </h1>
          
          {movie.overview && (
            <p className="text-chef-muted text-base md:text-lg max-w-2xl leading-relaxed line-clamp-2 mb-8">
              {movie.overview}
            </p>
          )}

          {movie.genres && movie.genres.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-6">
              {movie.genres.slice(0, 3).map((genre, index) => (
                <span
                  key={index}
                  className="px-3 py-1 text-xs tracking-wide uppercase 
                             bg-chef-surface/50 backdrop-blur-sm rounded-full
                             border border-white/5 text-chef-muted"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;