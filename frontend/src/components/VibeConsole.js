import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Smile, Zap, RefreshCw } from "lucide-react";
import { Switch } from "./ui/switch";

const VerticalSlider = ({ value, onChange, label, icon: Icon, lowLabel, highLabel, color }) => {
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Icon and Label */}
      <div className="flex flex-col items-center gap-2">
        <Icon className={`w-6 h-6 ${color}`} strokeWidth={1.5} />
        <span className="text-sm tracking-wide uppercase text-flick-muted">{label}</span>
      </div>
      
      {/* High Label */}
      <span className="text-xs text-flick-muted/60">{highLabel}</span>
      
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
            background: color === 'text-flick-teal' 
              ? 'rgba(45, 212, 191, 0.4)' 
              : color === 'text-flick-orange' 
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
          className="absolute left-1/2 -translate-x-1/2 w-10 h-2 bg-flick-platinum rounded-full shadow-lg"
          style={{ bottom: `calc(${value}% - 4px)` }}
        />
      </div>
      
      {/* Low Label */}
      <span className="text-xs text-flick-muted/60">{lowLabel}</span>
      
      {/* Value Display */}
      <span className="text-lg font-serif text-flick-platinum">{value}</span>
    </div>
  );
};

const VibeConsole = ({ open, onOpenChange, params, onParamsChange }) => {
  const [localParams, setLocalParams] = useState(params);
  
  useEffect(() => {
    setLocalParams(params);
  }, [params]);

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
  };

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
                       bg-flick-surface/90 backdrop-blur-xl border border-white/10
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
              <X className="w-5 h-5 text-flick-muted" strokeWidth={1.5} />
            </button>

            {/* Header */}
            <div className="text-center mb-12">
              <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-2">
                Tune Your Vibe
              </h2>
              <p className="text-flick-muted">
                Adjust the sliders to match your current mood
              </p>
            </div>

            {/* Sliders */}
            <div className="flex justify-center gap-16 md:gap-24 mb-12">
              <VerticalSlider
                value={localParams.brain_power}
                onChange={(val) => setLocalParams({ ...localParams, brain_power: val })}
                label="Brain Power"
                icon={Brain}
                lowLabel="Zoned Out"
                highLabel="Deep Focus"
                color="text-flick-teal"
              />
              
              <VerticalSlider
                value={localParams.mood}
                onChange={(val) => setLocalParams({ ...localParams, mood: val })}
                label="Mood"
                icon={Smile}
                lowLabel="Need a Cry"
                highLabel="Pure Joy"
                color="text-flick-gold"
              />
              
              <VerticalSlider
                value={localParams.energy}
                onChange={(val) => setLocalParams({ ...localParams, energy: val })}
                label="Energy"
                icon={Zap}
                lowLabel="Exhausted"
                highLabel="Hyped"
                color="text-flick-orange"
              />
            </div>

            {/* Rewatches Toggle */}
            <div className="flex items-center justify-center gap-4 mb-10">
              <span className="text-flick-muted">Include Rewatches</span>
              <Switch
                checked={localParams.include_rewatches}
                onCheckedChange={(checked) => 
                  setLocalParams({ ...localParams, include_rewatches: checked })
                }
                data-testid="include-rewatches-toggle"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-center gap-4">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-3 rounded-full
                           border border-white/10 text-flick-muted
                           hover:bg-white/5 hover:text-flick-platinum
                           transition-all duration-300"
                data-testid="vibe-reset-btn"
              >
                <RefreshCw className="w-4 h-4" strokeWidth={1.5} />
                Reset
              </button>
              
              <button
                onClick={handleApply}
                className="px-8 py-3 rounded-full
                           bg-flick-teal/20 border border-flick-teal/30
                           text-flick-teal font-medium
                           hover:bg-flick-teal/30 hover:border-flick-teal/50
                           shadow-glow-teal
                           transition-all duration-300"
                data-testid="vibe-apply-btn"
              >
                Apply Vibe
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default VibeConsole;
