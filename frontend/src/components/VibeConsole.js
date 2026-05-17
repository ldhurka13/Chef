import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Smile, Zap, RefreshCw, Sparkles, Loader2, Star, Film } from "lucide-react";
import { Switch } from "./ui/switch";
import axios from "axios";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem("chef_token");
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

const VerticalSlider = ({ value, onChange, label, icon: Icon, lowLabel, highLabel, color }) => {
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Icon and Label */}
      <div className="flex flex-col items-center gap-2">
        <Icon className={`w-6 h-6 ${color}`} strokeWidth={1.5} />
        <span className="text-sm tracking-wide uppercase text-chef-muted">{label}</span>
      </div>
      
      {/* High Label */}
      <span className="text-xs text-chef-muted/60">{highLabel}</span>
      
      {/* Vertical Slider */}
      <div className="relative h-64 w-12 flex flex-col items-center">
        {/* Track Background */}
        <div 
          className="absolute inset-0 rounded-full overflow-hidden"
          style={{
            background: `linear-gradient(to top, rgba(45, 212, 191, 0.2), rgba(249, 115, 22, 0.2))`,
          }}
        />
        
        {/* Fill Level */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 rounded-full"
          style={{
            background: color === 'text-chef-teal' 
              ? 'rgba(45, 212, 191, 0.4)' 
              : color === 'text-chef-orange' 
                ? 'rgba(249, 115, 22, 0.4)'
                : 'rgba(192, 178, 131, 0.4)',
          }}
          animate={{ height: `${value}%` }}
          transition={{ duration: 0.2 }}
        />
        
        {/* Input */}
        <input
          type="range"
          min="0"
          max="100"
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="absolute inset-0 opacity-0 cursor-pointer"
          style={{
            writingMode: "vertical-lr",
            direction: "rtl",
          }}
        />
        
        {/* Thumb Indicator */}
        <motion.div
          className="absolute left-1/2 -translate-x-1/2 w-10 h-2 bg-chef-platinum rounded-full shadow-lg"
          style={{ bottom: `calc(${value}% - 4px)` }}
        />
      </div>
      
      {/* Low Label */}
      <span className="text-xs text-chef-muted/60">{lowLabel}</span>
      
      {/* Value Display */}
      <span className="text-lg font-serif text-chef-platinum">{value}</span>
    </div>
  );
};

const VibeConsole = ({ open, onOpenChange, params, onParamsChange }) => {
  const [localParams, setLocalParams] = useState(params);
  const [aiMode, setAiMode] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResults, setAiResults] = useState([]);
  const [vibeDescription, setVibeDescription] = useState("");
  
  useEffect(() => {
    setLocalParams(params);
  }, [params]);

  useEffect(() => {
    if (!open) {
      setAiMode(false);
      setAiResults([]);
    }
  }, [open]);

  const handleApply = () => {
    onParamsChange(localParams);
    onOpenChange(false);
  };

  const handleReset = () => {
    const defaultParams = {
      brain_power: 50,
      mood: 50,
      energy: 50,
      include_rewatches: false,
    };
    setLocalParams(defaultParams);
    setAiResults([]);
    setAiMode(false);
  };

  const handleAIRecommend = async () => {
    setAiLoading(true);
    setAiMode(true);
    try {
      const res = await axios.post(
        `${API}/api/movies/ai-vibe-recommendations`,
        localParams,
        { headers: authHeaders() }
      );
      setAiResults(res.data.results || []);
      setVibeDescription(res.data.vibe_description || "");
      if (res.data.results?.length > 0) {
        toast.success(`Found ${res.data.results.length} AI-curated recommendations!`);
      }
    } catch (error) {
      console.error("AI recommendation failed:", error);
      toast.error("AI recommendations unavailable. Try again later.");
      setAiMode(false);
    } finally {
      setAiLoading(false);
    }
  };

  const AIResultCard = ({ movie, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="flex gap-4 p-4 bg-chef-bg/50 border border-white/5 rounded-xl
                 hover:border-chef-teal/30 transition-all cursor-pointer group"
      data-testid={`ai-result-${index}`}
    >
      {movie.poster_path ? (
        <img
          src={`https://image.tmdb.org/t/p/w200${movie.poster_path}`}
          alt={movie.title}
          className="w-16 h-24 rounded-lg object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-16 h-24 rounded-lg bg-chef-surface flex items-center justify-center flex-shrink-0">
          <Film className="w-6 h-6 text-chef-muted/30" />
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        <h4 className="font-serif text-base text-chef-platinum truncate group-hover:text-chef-teal transition-colors">
          {movie.title}
        </h4>
        
        <div className="flex items-center gap-2 mt-1">
          {movie.vote_average > 0 && (
            <span className="flex items-center gap-1 text-xs text-chef-gold">
              <Star className="w-3 h-3" fill="currentColor" />
              {movie.vote_average.toFixed(1)}
            </span>
          )}
          {movie.release_date && (
            <span className="text-xs text-chef-muted">{movie.release_date.slice(0, 4)}</span>
          )}
          {movie.ai_recommended && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500/10 
                           border border-purple-400/20 rounded text-[10px] text-purple-400">
              <Sparkles className="w-2.5 h-2.5" />
              AI
            </span>
          )}
        </div>
        
        {movie.vibe_reason && (
          <p className="text-xs text-chef-teal/80 mt-2 italic line-clamp-2">
            "{movie.vibe_reason}"
          </p>
        )}
        
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {movie.genres.slice(0, 3).map((genre, i) => (
              <span key={i} className="text-[10px] px-1.5 py-0.5 bg-white/5 rounded text-chef-muted/70">
                {typeof genre === 'string' ? genre : genre.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[60] flex items-center justify-center"
          onClick={() => onOpenChange(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/80 backdrop-blur-md" />
          
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="relative w-full max-w-3xl mx-4 p-8 md:p-12 rounded-3xl
                       bg-chef-surface/90 backdrop-blur-xl border border-white/10
                       shadow-cinematic"
            onClick={(e) => e.stopPropagation()}
            data-testid="vibe-console-modal"
          >
            {/* Close Button */}
            <button
              onClick={() => onOpenChange(false)}
              className="absolute top-6 right-6 p-2 rounded-full 
                         hover:bg-white/10 transition-colors"
              data-testid="vibe-close-btn"
            >
              <X className="w-5 h-5 text-chef-muted" strokeWidth={1.5} />
            </button>

            {/* Header */}
            <div className="text-center mb-8">
              <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-2">
                {aiMode && aiResults.length > 0 ? "AI Vibe Picks" : "Tune Your Vibe"}
              </h2>
              <p className="text-chef-muted">
                {aiMode && aiResults.length > 0 
                  ? vibeDescription || "Hidden gems matched to your current mood"
                  : "Adjust the sliders to match your current mood"}
              </p>
            </div>

            {/* AI Results Mode */}
            {aiMode && aiResults.length > 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4 mb-8 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar"
              >
                {aiResults.map((movie, index) => (
                  <AIResultCard key={movie.id || index} movie={movie} index={index} />
                ))}
              </motion.div>
            ) : (
              <>
                {/* Sliders */}
                <div className="flex justify-center gap-16 md:gap-24 mb-8">
                  <VerticalSlider
                    value={localParams.brain_power}
                    onChange={(val) => setLocalParams({ ...localParams, brain_power: val })}
                    label="Brain Power"
                    icon={Brain}
                    lowLabel="Zoned Out"
                    highLabel="Deep Focus"
                    color="text-chef-teal"
                  />
                  
                  <VerticalSlider
                    value={localParams.mood}
                    onChange={(val) => setLocalParams({ ...localParams, mood: val })}
                    label="Emotion"
                    icon={Smile}
                    lowLabel="Need a Cry"
                    highLabel="Need a Laugh"
                    color="text-chef-gold"
                  />
                  
                  <VerticalSlider
                    value={localParams.energy}
                    onChange={(val) => setLocalParams({ ...localParams, energy: val })}
                    label="Energy"
                    icon={Zap}
                    lowLabel="Exhausted"
                    highLabel="Locked In"
                    color="text-chef-orange"
                  />
                </div>

                {/* Rewatches Toggle */}
                <div className="flex items-center justify-center gap-4 mb-8">
                  <span className="text-chef-muted">Include Rewatches</span>
                  <Switch
                    checked={localParams.include_rewatches}
                    onCheckedChange={(checked) => 
                      setLocalParams({ ...localParams, include_rewatches: checked })
                    }
                    data-testid="include-rewatches-toggle"
                  />
                </div>
              </>
            )}

            {/* Actions */}
            <div className="flex justify-center gap-4">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-3 rounded-full
                           border border-white/10 text-chef-muted
                           hover:bg-white/5 hover:text-chef-platinum
                           transition-all duration-300"
                data-testid="vibe-reset-btn"
              >
                <RefreshCw className="w-4 h-4" strokeWidth={1.5} />
                Reset
              </button>
              
              {aiMode && aiResults.length > 0 ? (
                <button
                  onClick={() => { setAiMode(false); setAiResults([]); }}
                  className="flex items-center gap-2 px-6 py-3 rounded-full
                             bg-chef-surface border border-white/10
                             text-chef-muted hover:text-chef-platinum
                             transition-all duration-300"
                  data-testid="back-to-sliders-btn"
                >
                  Back to Sliders
                </button>
              ) : (
                <button
                  onClick={handleApply}
                  className="px-8 py-3 rounded-full
                             bg-chef-teal/20 border border-chef-teal/30
                             text-chef-teal font-medium
                             hover:bg-chef-teal/30 hover:border-chef-teal/50
                             shadow-glow-teal
                             transition-all duration-300"
                  data-testid="vibe-apply-btn"
                >
                  Apply Vibe
                </button>
              )}
              
              <button
                onClick={handleAIRecommend}
                disabled={aiLoading}
                className="flex items-center gap-2 px-6 py-3 rounded-full
                           bg-purple-500/20 border border-purple-400/30
                           text-purple-400 font-medium
                           hover:bg-purple-500/30 hover:border-purple-400/50
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all duration-300"
                data-testid="ai-recommend-btn"
              >
                {aiLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    AI Recommend
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default VibeConsole;
