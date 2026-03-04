import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Sparkles } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";
import MovieGrid from "./MovieGrid";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FeelingSearch = ({ onMovieClick }) => {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const res = await axios.post(`${API}/movies/feeling-search`, {
        query: query.trim(),
        page: 1
      });
      setResults(res.data.results || []);
      setShowResults(true);
    } catch (error) {
      console.error("Feeling search failed:", error);
      toast.error("Couldn't find movies for that feeling");
    } finally {
      setIsSearching(false);
    }
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
    if (e.key === "Escape") {
      setShowResults(false);
      setQuery("");
    }
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setShowResults(false);
  };

  const placeholderSuggestions = [
    "Tell us what you're feeling here...",
    "I want something exciting...",
    "Feeling nostalgic tonight...",
    "Need a good cry...",
    "Something to watch with friends...",
  ];

  const [placeholderIndex] = useState(0);

  return (
    <>
      {/* Search Bar */}
      <div className="relative z-30 w-full max-w-2xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className={`relative flex items-center gap-3 px-6 py-4 rounded-full
                     transition-all duration-500 ease-out
                     ${isFocused 
                       ? 'bg-flick-surface/80 backdrop-blur-xl border border-flick-teal/30 shadow-glow-teal' 
                       : 'bg-flick-surface/40 backdrop-blur-md border border-white/10'}`}
        >
          {/* Sparkle Icon */}
          <Sparkles 
            className={`w-5 h-5 flex-shrink-0 transition-colors duration-300
                       ${isFocused ? 'text-flick-teal' : 'text-flick-muted'}`}
            strokeWidth={1.5}
          />
          
          {/* Input */}
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholderSuggestions[placeholderIndex]}
            className="flex-1 bg-transparent text-flick-platinum placeholder-flick-muted/50
                       text-base md:text-lg font-light tracking-wide
                       focus:outline-none"
            data-testid="feeling-search-input"
          />
          
          {/* Clear/Search Button */}
          {query ? (
            <button
              onClick={handleClear}
              className="p-2 rounded-full hover:bg-white/10 transition-colors"
              data-testid="feeling-search-clear"
            >
              <X className="w-4 h-4 text-flick-muted" strokeWidth={1.5} />
            </button>
          ) : null}
          
          <button
            onClick={handleSearch}
            disabled={!query.trim() || isSearching}
            className={`p-3 rounded-full transition-all duration-300
                       ${query.trim() 
                         ? 'bg-flick-teal/20 text-flick-teal hover:bg-flick-teal/30' 
                         : 'bg-white/5 text-flick-muted'}`}
            data-testid="feeling-search-btn"
          >
            {isSearching ? (
              <div className="w-5 h-5 border-2 border-flick-teal border-t-transparent rounded-full animate-spin" />
            ) : (
              <Search className="w-5 h-5" strokeWidth={1.5} />
            )}
          </button>
        </motion.div>
        
        {/* Quick Suggestions */}
        <AnimatePresence>
          {isFocused && !query && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute top-full left-0 right-0 mt-2 px-4"
            >
              <div className="glass rounded-2xl p-4">
                <p className="text-xs text-flick-muted uppercase tracking-wider mb-3">
                  Try saying...
                </p>
                <div className="flex flex-wrap gap-2">
                  {[
                    "feeling nostalgic",
                    "need a laugh",
                    "something intense",
                    "cozy rainy day",
                    "date night",
                    "mind-bending"
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setQuery(suggestion);
                        setIsFocused(false);
                      }}
                      className="px-3 py-1.5 text-sm rounded-full
                               bg-white/5 border border-white/10 text-flick-muted
                               hover:bg-white/10 hover:text-flick-platinum
                               transition-all duration-200"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Results Overlay */}
      <AnimatePresence>
        {showResults && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-flick-bg/95 backdrop-blur-sm overflow-y-auto"
          >
            <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="font-serif text-2xl md:text-3xl tracking-tight">
                    Movies for "{query}"
                  </h2>
                  <p className="text-flick-muted mt-1">
                    {results.length} movies match your vibe
                  </p>
                </div>
                <button
                  onClick={() => setShowResults(false)}
                  className="p-3 rounded-full glass hover:bg-white/10 transition-colors"
                  data-testid="close-feeling-results"
                >
                  <X className="w-5 h-5 text-flick-platinum" strokeWidth={1.5} />
                </button>
              </div>
              
              {/* Results Grid */}
              <MovieGrid 
                movies={results}
                loading={false}
                onMovieClick={(movie) => {
                  onMovieClick(movie);
                  setShowResults(false);
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FeelingSearch;
