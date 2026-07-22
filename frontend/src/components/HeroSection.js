import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
 
const KINOCHECK_API_KEY = "COtU1fo6DTQqYJkexdDWa3y2ygAqzijfXtGunSKKn14GNvAB02XPgYx7hSsrpEbL";
 
const HeroSection = ({ movie, loading, onMovieClick }) => {
  const [trailerId, setTrailerId] = useState(null);
 
  useEffect(() => {
    if (!movie?.tmdb_id) return;
    setTrailerId(null);
    fetch(
      `https://api.kinocheck.com/movies?tmdb_id=${movie.tmdb_id}&categories=Trailer&language=en`,
      {
        headers: {
          "X-Api-Key": KINOCHECK_API_KEY,
          "X-Api-Host": "api.kinocheck.com",
        },
      }
    )
      .then((res) => res.json())
      .then((data) => {
        if (data?.trailer?.youtube_video_id) setTrailerId(data.trailer.youtube_video_id);
      })
      .catch(() => {});
  }, [movie?.tmdb_id]);
 
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
      className="relative min-h-[70vh] w-full overflow-hidden cursor-pointer bg-chef-bg"
      data-testid="hero-section"
      onClick={() => onMovieClick(movie)}
    >
      {/* Background Media */}
      <motion.div
        initial={{ scale: 1.1, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.2, ease: "easeOut" }}
        className="absolute inset-0 pointer-events-none z-0"
      >
        {trailerId ? (
          <div className="w-full h-full relative overflow-hidden">
            <iframe
              className="absolute top-1/2 left-1/2 w-[130vw] h-[130vh] -translate-x-1/2 -translate-y-1/2 object-cover"
              src={`https://www.youtube.com/embed/${trailerId}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&loop=1&playlist=${trailerId}`}
              title={`${movie.title} Trailer`}
              frameBorder="0"
              allow="autoplay; encrypted-media"
              allowFullScreen
            />
          </div>
        ) : movie.backdrop_url ? (
          /* Fallback image if no trailer is found */
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
      <div className="absolute inset-0 bg-gradient-to-t from-chef-bg via-chef-bg/60 to-transparent z-10" />
      <div className="absolute inset-0 bg-gradient-to-r from-chef-bg/80 via-transparent to-transparent z-10" />
      {/* Vignette */}
      <div
        className="absolute inset-0 pointer-events-none z-10"
        style={{
          background: "radial-gradient(circle at center, transparent 0%, #0A0A0B 100%)",
          opacity: 0.4,
        }}
      />
      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-8 md:p-16 max-w-4xl z-20 pointer-events-none">
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