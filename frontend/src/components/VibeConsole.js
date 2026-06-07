import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Smile, Zap, RefreshCw, Loader2, User, Users, Heart } from "lucide-react";

// Watch Context Selector Component
const WatchContextSelector = ({ value, onChange }) => {
  const options = [
    { id: "solo", label: "Solo", icon: User },
    { id: "date", label: "Date", icon: Heart },
    { id: "group", label: "Group", icon: Users },
  ];

  return (
    <div className="flex justify-center gap-2">
      {options.map(({ id, label, icon: Icon }) => (
        <motion.button
          key={id}
          onClick={() => onChange(id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all
            ${value === id 
              ? "bg-chef-teal/10 border-chef-teal/40 text-chef-teal" 
              : "bg-chef-surface/40 border-white/10 text-chef-muted hover:border-white/20 hover:text-chef-platinum"
            }`}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          data-testid={`watch-context-${id}`}
        >
          <Icon className="w-4 h-4" strokeWidth={1.5} />
          <span className="text-sm font-medium">{label}</span>
        </motion.button>
      ))}
    </div>
  );
};

const VerticalSlider = ({ value, onChange, label, icon: Icon, lowLabel, highLabel, color }) => {
  return (
    <div className="flex flex-col items-center gap-4">
      {/* High Label */}
      <span className="text-sm font-medium text-chef-muted/80">{highLabel}</span>
      
      {/* Icon */}
      <div className={`p-3 rounded-full bg-white/5 ${color}`}>
        <Icon className="w-6 h-6" strokeWidth={1.5} />
      </div>
      
      {/* Vertical Slider Track - Bigger and Wider */}
      <div className="relative h-48 w-6 bg-white/10 rounded-full overflow-hidden shadow-inner">
        {/* Fill */}
        <motion.div
          className={`absolute bottom-0 left-0 right-0 rounded-full ${
            color.includes("teal") ? "bg-chef-teal" :
            color.includes("gold") ? "bg-chef-gold" :
            "bg-chef-orange"
          }`}
          style={{ height: `${value}%` }}
          layout
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
        
        {/* Invisible Range Input */}
        <input
          type="range"
          min="0"
          max="100"
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer 
                     [writing-mode:vertical-lr] [direction:rtl]"
          data-testid={`slider-${label.toLowerCase().replace(' ', '-')}`}
        />
      </div>
      
      {/* Low Label */}
      <span className="text-sm font-medium text-chef-muted/80">{lowLabel}</span>
      
      {/* Value Display */}
      <span className="text-xl font-serif text-chef-platinum">{value}</span>
    </div>
  );
};

const VibeConsole = ({ open, onOpenChange, params, onParamsChange, onReset }) => {
  const [localParams, setLocalParams] = useState({...params, watch_context: params.watch_context || "solo"});
  const [applyLoading, setApplyLoading] = useState(false);
  
  useEffect(() => {
    setLocalParams({...params, watch_context: params.watch_context || "solo"});
  }, [params]);

  const handleApply = async () => {
    setApplyLoading(true);
    // Pass useAI=true to trigger AI recommendations for Chef's Curation
    await onParamsChange(localParams, true);
    setApplyLoading(false);
    onOpenChange(false);
  };

  const handleReset = () => {
    const defaultParams = {
      brain_power: 50,
      mood: 50,
      energy: 50,
      watch_context: "solo",
    };
    setLocalParams(defaultParams);
    if (onReset) {
      onReset();
    }
    onOpenChange(false);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-[60] flex items-center justify-center py-8 md:py-12"
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
            className="relative w-full max-w-3xl mx-4 p-6 md:p-10 rounded-2xl
                       bg-chef-surface/90 backdrop-blur-xl border border-white/10
                       shadow-cinematic max-h-[calc(100vh-4rem)] md:max-h-[calc(100vh-6rem)] overflow-y-auto"
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
                Tune Your Vibe
              </h2>
              <p className="text-chef-muted">
                Adjust the sliders to match your current mood
              </p>
            </div>

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
                lowLabel="Serious"
                highLabel="Fun"
                color="text-chef-gold"
              />
              
              <VerticalSlider
                value={localParams.energy}
                onChange={(val) => setLocalParams({ ...localParams, energy: val })}
                label="Energy"
                icon={Zap}
                lowLabel="Exhausted"
                highLabel="LFG"
                color="text-chef-orange"
              />
            </div>

            {/* Watch Context */}
            <div className="mb-8">
              <p className="text-center text-sm text-chef-muted mb-4">Who&apos;s watching?</p>
              <WatchContextSelector
                value={localParams.watch_context}
                onChange={(val) => setLocalParams({ ...localParams, watch_context: val })}
              />
            </div>

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
              
              <button
                onClick={handleApply}
                disabled={applyLoading}
                className="flex items-center gap-2 px-8 py-3 rounded-full
                           bg-purple-500/20 border border-purple-400/30
                           text-purple-400 font-medium
                           hover:bg-purple-500/30 hover:border-purple-400/50
                           disabled:opacity-50 disabled:cursor-not-allowed
                           shadow-glow-teal
                           transition-all duration-300"
                data-testid="vibe-apply-btn"
              >
                {applyLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Curating...
                  </>
                ) : (
                  "Apply Vibe"
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
