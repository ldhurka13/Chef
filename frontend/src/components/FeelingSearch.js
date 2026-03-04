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
      <div className="relative z-30 w-full max-w-xl mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className={`relative flex items-center gap-2 px-4 py-2
                     transition-all duration-300 ease-out
                     border-b ${isFocused 
                       ? 'border-flick-teal/50' 
                       : 'border-white/20'}`}
        >
          {/* Sparkle Icon */}
          <Sparkles 
            className={`w-4 h-4 flex-shrink-0 transition-colors duration-300
                       ${isFocused ? 'text-flick-teal' : 'text-flick-muted/60'}`}
            strokeWidth={1}
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
            className="flex-1 bg-transparent text-flick-platinum placeholder-flick-muted/40
                       text-sm font-light tracking-wide
                       focus:outline-none"
            data-testid="feeling-search-input"
          />
          
          {/* Clear Button */}
          {query ? (
            <button
              onClick={handleClear}
              className="p-1 hover:text-flick-platinum transition-colors"
              data-testid="feeling-search-clear"
            >
              <X className="w-3 h-3 text-flick-muted" strokeWidth={1.5} />
            </button>
          ) : null}
          
          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={!query.trim() || isSearching}
            className={`p-1.5 transition-all duration-300
                       ${query.trim() 
                         ? 'text-flick-teal hover:text-flick-platinum' 
                         : 'text-flick-muted/40'}`}
            data-testid="feeling-search-btn"
          >
            {isSearching ? (
              <div className="w-4 h-4 border border-flick-teal border-t-transparent rounded-full animate-spin" />
            ) : (
              <Search className="w-4 h-4" strokeWidth={1.5} />
            )}
          </button>
        </motion.div>
        
        {/* Quick Suggestions */}
        <AnimatePresence>
          {isFocused && !query && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute top-full left-0 right-0 mt-3 px-4"
            >
              <div className="bg-flick-surface/90 backdrop-blur-md border-l border-white/10 p-4">
                <p className="text-[10px] text-flick-muted/60 uppercase tracking-[0.2em] mb-3">
                  Try saying
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
                      className="px-3 py-1 text-xs text-flick-muted/80
                               border-b border-transparent
                               hover:text-flick-platinum hover:border-flick-teal/30
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
            className="fixed inset-0 z-40 bg-flick-bg/98 backdrop-blur-sm overflow-y-auto"
          >
            <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-8 border-b border-white/10 pb-4">
                <div>
                  <h2 className="font-serif text-xl md:text-2xl tracking-tight">
                    Movies for "{query}"
                  </h2>
                  <p className="text-flick-muted/60 text-sm mt-1">
                    {results.length} matches
                  </p>
                </div>
                <button
                  onClick={() => setShowResults(false)}
                  className="p-2 text-flick-muted hover:text-flick-platinum 
                           border-b border-transparent hover:border-flick-teal/30
                           transition-all duration-200"
                  data-testid="close-feeling-results"
                >
                  <X className="w-5 h-5" strokeWidth={1} />
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
