/**
 * FeelingSearch.js (Unified Search)
 * 
 * A unified search input supporting:
 * 1. Traditional title/person search with live dropdown suggestions
 * 2. Natural-language mood/vibe search using AI Vibe Engine
 * 
 * Intent is automatically determined based on TMDB matches.
 */
import React, { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Sparkles, Film, User, Tv, Loader2, AlertCircle } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Helper to get auth headers
const authHeaders = () => {
  const token = localStorage.getItem("chef_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Debounce hook
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
};

const FeelingSearch = ({ 
  onMovieClick, 
  onPersonClick,
  onVibeResults 
}) => {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  
  // Dropdown state
  const [suggestions, setSuggestions] = useState({ titles: [], people: [] });
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  // Vibe search state
  const [isVibeSearching, setIsVibeSearching] = useState(false);
  const [vibeResults, setVibeResults] = useState(null);
  const [vibeError, setVibeError] = useState(null);
  
  // Request cancellation
  const abortControllerRef = useRef(null);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  
  // Debounced query for suggestions
  const debouncedQuery = useDebounce(query.trim(), 300);
  
  // Quick prompt chips
  const quickPrompts = [
    "feeling nostalgic",
    "need a laugh",
    "something intense",
    "cozy rainy day",
    "date night",
    "mind-bending"
  ];
  
  // Fetch suggestions when debounced query changes
  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.length < 2) {
      setSuggestions({ titles: [], people: [] });
      setShowDropdown(false);
      return;
    }
    
    const fetchSuggestions = async () => {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();
      
      setLoadingSuggestions(true);
      
      try {
        const res = await axios.get(`${API}/search/suggestions`, {
          params: { q: debouncedQuery, limit: 8 },
          signal: abortControllerRef.current.signal,
          headers: authHeaders()
        });
        
        setSuggestions({
          titles: res.data.titles || [],
          people: res.data.people || []
        });
        setShowDropdown(true);
        setSelectedIndex(-1);
      } catch (err) {
        if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
          console.error("Suggestions fetch failed:", err);
        }
      } finally {
        setLoadingSuggestions(false);
      }
    };
    
    fetchSuggestions();
    
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [debouncedQuery]);
  
  // Get all dropdown items as a flat list
  const getAllItems = useCallback(() => {
    const items = [];
    suggestions.titles.forEach(t => items.push({ type: 'title', data: t }));
    suggestions.people.forEach(p => items.push({ type: 'person', data: p }));
    return items;
  }, [suggestions]);
  
  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    const items = getAllItems();
    
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (showDropdown && items.length > 0) {
        setSelectedIndex(prev => 
          prev < items.length - 1 ? prev + 1 : prev
        );
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (showDropdown && items.length > 0) {
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && items[selectedIndex]) {
        // Select highlighted item
        handleItemSelect(items[selectedIndex]);
      } else {
        // Submit query
        handleSubmit();
      }
    } else if (e.key === "Escape") {
      setShowDropdown(false);
      setSelectedIndex(-1);
    }
  };
  
  // Handle item selection from dropdown
  const handleItemSelect = (item) => {
    setShowDropdown(false);
    setQuery("");
    setSelectedIndex(-1);
    
    if (item.type === 'title') {
      if (onMovieClick) {
        onMovieClick({
          id: item.data.id,
          media_type: item.data.media_type,
          title: item.data.title,
          poster_path: item.data.poster_path,
          poster_url: item.data.poster_url,
        });
      }
    } else if (item.type === 'person') {
      if (onPersonClick) {
        onPersonClick(item.data);
      }
    }
  };
  
  // Handle search submit
  const handleSubmit = async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || trimmedQuery.length < 2) return;
    
    setShowDropdown(false);
    
    // Check if we have a strong entity match
    const items = getAllItems();
    const hasStrongMatch = items.length > 0 && 
      items[0].data && 
      (items[0].data.title?.toLowerCase() === trimmedQuery.toLowerCase() ||
       items[0].data.name?.toLowerCase() === trimmedQuery.toLowerCase());
    
    if (hasStrongMatch) {
      // Open the best match
      handleItemSelect(items[0]);
      return;
    }
    
    // Check intent via API
    try {
      const intentRes = await axios.get(`${API}/search/intent`, {
        params: { q: trimmedQuery },
        headers: authHeaders()
      });
      
      if (intentRes.data.is_entity && intentRes.data.best_match) {
        // It's an entity search - open the match
        handleItemSelect(intentRes.data.best_match);
        return;
      }
    } catch (err) {
      // Fallback to vibe search on error
      console.error("Intent check failed:", err);
    }
    
    // Default to vibe/mood search
    await performVibeSearch(trimmedQuery);
  };
  
  // Perform AI vibe search
  const performVibeSearch = async (searchQuery) => {
    setIsVibeSearching(true);
    setVibeError(null);
    setVibeResults(null);
    
    try {
      const res = await axios.post(`${API}/search/vibe`, {
        query: searchQuery,
        limit: 5
      }, {
        headers: authHeaders()
      });
      
      const results = res.data.results || [];
      
      if (results.length === 0) {
        setVibeError("No movies found for that mood. Try a different description.");
        return;
      }
      
      setVibeResults({
        query: searchQuery,
        movies: results
      });
      
      // Notify parent component
      if (onVibeResults) {
        onVibeResults({
          query: searchQuery,
          movies: results
        });
      }
    } catch (err) {
      console.error("Vibe search failed:", err);
      setVibeError(err.response?.data?.detail || "Search failed. Please try again.");
      toast.error("Couldn't find movies for that mood");
    } finally {
      setIsVibeSearching(false);
    }
  };
  
  // Handle quick prompt click
  const handleQuickPrompt = (prompt) => {
    setQuery(prompt);
    setIsFocused(false);
    // Trigger vibe search directly for prompts
    performVibeSearch(prompt);
  };
  
  // Handle clear
  const handleClear = () => {
    setQuery("");
    setSuggestions({ titles: [], people: [] });
    setShowDropdown(false);
    setVibeResults(null);
    setVibeError(null);
    setSelectedIndex(-1);
    inputRef.current?.focus();
    
    // Notify parent to clear results
    if (onVibeResults) {
      onVibeResults(null);
    }
  };
  
  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  
  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex >= 0 && dropdownRef.current) {
      const selectedEl = dropdownRef.current.querySelector(`[data-index="${selectedIndex}"]`);
      if (selectedEl) {
        selectedEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);
  
  const hasResults = suggestions.titles.length > 0 || suggestions.people.length > 0;
  
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
                       ? 'border-chef-teal/50' 
                       : 'border-white/20'}`}
        >
          {/* Sparkle Icon */}
          <Sparkles 
            className={`w-4 h-4 flex-shrink-0 transition-colors duration-300
                       ${isFocused ? 'text-chef-teal' : 'text-chef-muted/60'}`}
            strokeWidth={1}
          />
          
          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 150)}
            placeholder="Search movies, shows, people, or tell Chef what you're feeling..."
            className="flex-1 bg-transparent text-chef-platinum placeholder-chef-platinum/50
                       text-sm font-normal tracking-wider
                       focus:outline-none"
            role="combobox"
            aria-expanded={showDropdown}
            aria-haspopup="listbox"
            aria-controls="search-dropdown"
            aria-activedescendant={selectedIndex >= 0 ? `search-item-${selectedIndex}` : undefined}
            data-testid="unified-search-input"
          />
          
          {/* Clear Button */}
          {(query || vibeResults) && (
            <button
              onClick={handleClear}
              className="p-1 hover:text-chef-platinum transition-colors"
              data-testid="search-clear"
              aria-label="Clear search"
            >
              <X className="w-3 h-3 text-chef-muted" strokeWidth={1.5} />
            </button>
          )}
          
          {/* Search Button */}
          <button
            onClick={handleSubmit}
            disabled={!query.trim() || isVibeSearching}
            className={`p-1.5 transition-all duration-300
                       ${query.trim() 
                         ? 'text-chef-teal hover:text-chef-platinum' 
                         : 'text-chef-muted/40'}`}
            data-testid="search-submit"
            aria-label="Search"
          >
            {isVibeSearching || loadingSuggestions ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" strokeWidth={1.5} />
            )}
          </button>
        </motion.div>
        
        {/* Dropdown */}
        <AnimatePresence>
          {showDropdown && (hasResults || loadingSuggestions) && (
            <motion.div
              ref={dropdownRef}
              id="search-dropdown"
              role="listbox"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 mx-4 
                         bg-chef-surface/95 backdrop-blur-xl border border-white/10 
                         rounded-lg shadow-xl max-h-80 overflow-y-auto"
              data-testid="search-dropdown"
            >
              {loadingSuggestions && !hasResults ? (
                // Loading state
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-5 h-5 text-chef-muted animate-spin" />
                </div>
              ) : (
                <>
                  {/* Titles section */}
                  {suggestions.titles.length > 0 && (
                    <div className="py-2">
                      <p className="px-3 py-1 text-[10px] text-chef-muted/60 uppercase tracking-wider">
                        Titles
                      </p>
                      {suggestions.titles.map((title, idx) => {
                        const globalIndex = idx;
                        const isSelected = selectedIndex === globalIndex;
                        
                        return (
                          <button
                            key={`title-${title.id}`}
                            id={`search-item-${globalIndex}`}
                            data-index={globalIndex}
                            data-testid={`search-title-${title.media_type}-${title.id}`}
                            role="option"
                            aria-selected={isSelected}
                            onClick={() => handleItemSelect({ type: 'title', data: title })}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-left
                                       transition-colors duration-100
                                       ${isSelected 
                                         ? 'bg-white/10' 
                                         : 'hover:bg-white/5'}`}
                          >
                            {/* Poster */}
                            <div className="w-8 h-12 rounded overflow-hidden bg-chef-bg/50 flex-shrink-0">
                              {title.poster_url || title.poster_path ? (
                                <img
                                  src={title.poster_url || `https://image.tmdb.org/t/p/w92${title.poster_path}`}
                                  alt=""
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  {title.media_type === 'tv' ? (
                                    <Tv className="w-4 h-4 text-chef-muted/30" />
                                  ) : (
                                    <Film className="w-4 h-4 text-chef-muted/30" />
                                  )}
                                </div>
                              )}
                            </div>
                            
                            {/* Info */}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-chef-platinum truncate">{title.title}</p>
                              <p className="text-xs text-chef-muted">
                                <span className="capitalize">{title.media_type === 'tv' ? 'TV' : 'Movie'}</span>
                                {title.year && <span className="ml-1">• {title.year}</span>}
                              </p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  
                  {/* People section */}
                  {suggestions.people.length > 0 && (
                    <div className="py-2 border-t border-white/5">
                      <p className="px-3 py-1 text-[10px] text-chef-muted/60 uppercase tracking-wider">
                        People
                      </p>
                      {suggestions.people.map((person, idx) => {
                        const globalIndex = suggestions.titles.length + idx;
                        const isSelected = selectedIndex === globalIndex;
                        
                        return (
                          <button
                            key={`person-${person.id}`}
                            id={`search-item-${globalIndex}`}
                            data-index={globalIndex}
                            data-testid={`search-person-${person.id}`}
                            role="option"
                            aria-selected={isSelected}
                            onClick={() => handleItemSelect({ type: 'person', data: person })}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-left
                                       transition-colors duration-100
                                       ${isSelected 
                                         ? 'bg-white/10' 
                                         : 'hover:bg-white/5'}`}
                          >
                            {/* Profile image */}
                            <div className="w-8 h-8 rounded-full overflow-hidden bg-chef-bg/50 flex-shrink-0">
                              {person.profile_url || person.profile_path ? (
                                <img
                                  src={person.profile_url || `https://image.tmdb.org/t/p/w92${person.profile_path}`}
                                  alt=""
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <User className="w-4 h-4 text-chef-muted/30" />
                                </div>
                              )}
                            </div>
                            
                            {/* Info */}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-chef-platinum truncate">{person.name}</p>
                              {(person.known_for_department || person.known_for) && (
                                <p className="text-xs text-chef-muted truncate">
                                  {person.known_for_department}
                                  {person.known_for && <span className="ml-1">• {person.known_for}</span>}
                                </p>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Quick Suggestions (when focused and empty) */}
        <AnimatePresence>
          {isFocused && !query && !vibeResults && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="absolute top-full left-0 right-0 mt-3 px-4"
            >
              <div className="bg-chef-surface/90 backdrop-blur-md border-l border-white/10 p-4">
                <p className="text-[10px] text-chef-muted/60 uppercase tracking-[0.2em] mb-3">
                  Try saying
                </p>
                <div className="flex flex-wrap gap-2">
                  {quickPrompts.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleQuickPrompt(suggestion)}
                      className="px-3 py-1 text-xs text-chef-muted/80
                               border-b border-transparent
                               hover:text-chef-platinum hover:border-chef-teal/30
                               transition-all duration-200"
                      data-testid={`quick-prompt-${suggestion.replace(/\s+/g, '-')}`}
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
      
      {/* Vibe Results Section - fixed overlay so it escapes the top bar container */}
      <AnimatePresence>
        {(vibeResults || vibeError || isVibeSearching) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-40 overflow-y-auto bg-chef-bg/95 backdrop-blur-xl pt-28 pb-16"
            data-testid="vibe-results-section"
          >
            <div className="w-full max-w-6xl mx-auto px-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-serif text-lg md:text-xl text-chef-platinum">
                  {isVibeSearching ? (
                    "Finding the perfect movies..."
                  ) : vibeResults ? (
                    <>Chef&apos;s picks for &quot;<span className="text-chef-teal">{vibeResults.query}</span>&quot;</>
                  ) : (
                    "Search Results"
                  )}
                </h2>
                {vibeResults && (
                  <p className="text-sm text-chef-muted mt-1">
                    {vibeResults.movies.length} AI-powered recommendations
                  </p>
                )}
              </div>
              
              <button
                onClick={handleClear}
                className="p-2 text-chef-muted hover:text-chef-platinum 
                         border-b border-transparent hover:border-chef-teal/30
                         transition-all duration-200"
                data-testid="clear-vibe-results"
                aria-label="Clear results"
              >
                <X className="w-5 h-5" strokeWidth={1} />
              </button>
            </div>
            
            {/* Loading state */}
            {isVibeSearching && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 text-chef-teal animate-spin mx-auto mb-3" />
                  <p className="text-chef-muted text-sm">Curating your perfect movies...</p>
                </div>
              </div>
            )}
            
            {/* Error state */}
            {vibeError && !isVibeSearching && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <AlertCircle className="w-10 h-10 text-red-400/60 mb-3" />
                <p className="text-chef-muted mb-4">{vibeError}</p>
                <button
                  onClick={() => performVibeSearch(query || vibeResults?.query || "")}
                  className="px-4 py-2 rounded-lg bg-chef-surface text-chef-platinum text-sm hover:bg-white/10 transition-colors"
                >
                  Try again
                </button>
              </div>
            )}
            
            {/* Results grid */}
            {vibeResults && !isVibeSearching && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                {vibeResults.movies.map((movie, idx) => (
                  <motion.div
                    key={movie.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="group cursor-pointer"
                    onClick={() => {
                      if (onMovieClick) {
                        onMovieClick({
                          id: movie.id,
                          media_type: movie.media_type || 'movie',
                          title: movie.title,
                          poster_path: movie.poster_path,
                          poster_url: movie.poster_url,
                        });
                      }
                    }}
                    data-testid={`vibe-result-${movie.id}`}
                  >
                    {/* Poster */}
                    <div className="aspect-[2/3] rounded-lg overflow-hidden bg-chef-surface/40 border border-white/10 group-hover:border-white/30 transition-all mb-2">
                      {movie.poster_url || movie.poster_path ? (
                        <img
                          src={movie.poster_url || `https://image.tmdb.org/t/p/w300${movie.poster_path}`}
                          alt={movie.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Film className="w-10 h-10 text-chef-muted/30" />
                        </div>
                      )}
                    </div>
                    
                    {/* Info */}
                    <div>
                      <p className="text-sm text-chef-platinum line-clamp-1 group-hover:text-white transition-colors">
                        {movie.title}
                      </p>
                      <p className="text-xs text-chef-muted line-clamp-2 mt-1">
                        {movie.vibe_reason || movie.overview?.slice(0, 80) || ""}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FeelingSearch;
