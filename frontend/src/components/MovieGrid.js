import React from "react";
import { motion } from "framer-motion";
import MovieCard from "./MovieCard";

const MovieGrid = ({ movies, loading, onMovieClick }) => {
  if (loading) {
    return (
      <div className="masonry-grid">
        {[...Array(8)].map((_, index) => (
          <div key={index} className="masonry-item">
            <div 
              className="aspect-[2/3] rounded-2xl skeleton"
              style={{ height: `${300 + Math.random() * 100}px` }}
            />
          </div>
        ))}
      </div>
    );
  }

  if (!movies || movies.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-chef-muted text-lg">No movies found. Try adjusting your vibe!</p>
      </div>
    );
  }

  return (
    <div className="masonry-grid" data-testid="movie-grid">
      {movies.map((movie, index) => (
        <motion.div
          key={movie.id}
          className="masonry-item"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ 
            duration: 0.5, 
            delay: index * 0.05,
            ease: "easeOut"
          }}
        >
          <MovieCard 
            movie={movie} 
            onClick={() => onMovieClick(movie)}
            index={index}
          />
        </motion.div>
      ))}
    </div>
  );
};

export default MovieGrid;
