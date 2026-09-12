import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Smile, Zap, Loader2, User, Users, Heart, Compass, Tv, Info, Check } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "./ui/tooltip";

// Watch Context Selector Component (compact segmented chips)
const WatchContextSelector = ({ value, onChange }) => {
  const options = [
    { id: "solo", label: "Solo", icon: User },
    { id: "date", label: "Date", icon: Heart },
    { id: "group", label: "Group", icon: Users },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {options.map(({ id, label, icon: Icon }) => {
        const active = value === id;
        return (
          <motion.button
            key={id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(id)}
            className={`inline-flex items-center gap-2 h-11 min-h-[44px] px-4 rounded-full border text-sm font-medium
              transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-chef-teal/40
              ${active
                ? "bg-chef-teal/15 border-chef-teal/50 text-chef-teal"
                : "bg-chef-surface/40 border-white/10 text-chef-muted hover:border-white/20 hover:text-chef-platinum"
              }`}
            whileTap={{ scale: 0.97 }}
            data-testid={`watch-context-${id}`}
          >
            <Icon className="w-4 h-4" strokeWidth={1.5} />
            <span>{label}</span>
          </motion.button>
        );
      })}
    </div>
  );
};

// Preference Chip Toggle
const PreferenceChip = ({
  icon: Icon,
  label,
  active,
  onToggle,
  activeColor, // "teal" | "gold"
  tooltip,
  disabled,
  testId,
}) => {
  const palette = activeColor === "gold"
    ? {
        border: "border-chef-gold/50",
        bg: "bg-chef-gold/15",
        text: "text-chef-gold",
        ring: "focus-visible:ring-chef-gold/40",
      }
    : {
        border: "border-chef-teal/50",
        bg: "bg-chef-teal/15",
        text: "text-chef-teal",
        ring: "focus-visible:ring-chef-teal/40",
      };

  return (
    <div className="relative inline-flex items-center">
      <motion.button
        type="button"
        role="switch"
        aria-checked={active}
        aria-label={label}
        aria-disabled={disabled}
        onClick={() => !disabled && onToggle(!active)}
        whileTap={{ scale: disabled ? 1 : 0.97 }}
        className={`inline-flex items-center gap-2 h-11 min-h-[44px] pl-3 pr-3 rounded-full border text-sm font-medium
          transition-colors focus:outline-none focus-visible:ring-2 ${palette.ring}
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          ${active
            ? `${palette.bg} ${palette.border} ${palette.text}`
            : "bg-chef-surface/40 border-white/10 text-chef-muted hover:border-white/20 hover:text-chef-platinum"
          }`}
        data-testid={testId}
      >
        <Icon className="w-4 h-4" strokeWidth={1.5} />
        <span>{label}</span>
        {active && <Check className="w-3.5 h-3.5" strokeWidth={2} />}
      </motion.button>
      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              aria-label={`About ${label}`}
              className="ml-1 p-1 rounded-full text-chef-muted/70 hover:text-chef-platinum
                       focus:outline-none focus-visible:ring-2 focus-visible:ring-chef-teal/40"
              data-testid={`${testId}-info`}
            >
              <Info className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </TooltipTrigger>
          <TooltipContent
            side="top"
            sideOffset={6}
            className="max-w-[220px] bg-chef-surface border border-white/10 text-chef-platinum text-xs leading-relaxed"
          >
            {tooltip}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

const VerticalSlider = ({ value, onChange, label, icon: Icon, lowLabel, highLabel, color }) => {
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Icon */}
      <div className={`p-3 rounded-full bg-white/5 ${color}`}>
        <Icon className="w-6 h-6" strokeWidth={1.5} />
      </div>

      {/* High Label */}
      <span className="text-sm font-medium text-chef-muted/80">{highLabel}</span>
    
      {/* Vertical Slider Track - Bigger and Wider */}
      <div className="relative h-48 w-8 bg-white/10 rounded-full overflow-hidden shadow-inner">
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

const VibeConsole = ({ open, onOpenChange, params, onParamsChange, user }) => {
  const [localParams, setLocalParams] = useState({
    ...params,
    watch_context: params.watch_context || "solo",
    feeling_adventurous: false,
    only_my_streaming: false,
  });
  const [applyLoading, setApplyLoading] = useState(false);
  
  useEffect(() => {
    // Reset toggles to OFF each time the console opens, keep vibe sliders/context
    if (open) {
      setLocalParams({
        ...params,
        watch_context: params.watch_context || "solo",
        feeling_adventurous: false,
        only_my_streaming: false,
      });
    }
  }, [open, params]);

  const streamingCount = (user?.streaming_services || []).length;

  const handleApply = async () => {
    setApplyLoading(true);
    // Pass useAI=true to trigger AI recommendations for Chef's Curation
    await onParamsChange(localParams, true);
    setApplyLoading(false);
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
                highLabel="Locked In"
                color="text-chef-teal"
              />
              
              <VerticalSlider
                value={localParams.mood}
                onChange={(val) => setLocalParams({ ...localParams, mood: val })}
                label="Emotion"
                icon={Smile}
                lowLabel="Serious"
                highLabel="Silly"
                color="text-chef-gold"
              />
              
              <VerticalSlider
                value={localParams.energy}
                onChange={(val) => setLocalParams({ ...localParams, energy: val })}
                label="Energy"
                icon={Zap}
                lowLabel="Exhausted"
                highLabel="Energized"
                color="text-chef-orange"
              />
            </div>

            {/* Compact 2-column config: Who's watching | Preferences */}
            <div className="max-w-2xl mx-auto mb-8">
              <div className="grid grid-cols-1 min-[900px]:grid-cols-2 gap-8 min-[900px]:gap-10 items-start">
                {/* Who's watching */}
                <div>
                  <p className="text-xs uppercase tracking-wider text-chef-muted mb-3">Who&apos;s watching?</p>
                  <div role="radiogroup" aria-label="Watch context">
                    <WatchContextSelector
                      value={localParams.watch_context}
                      onChange={(val) => setLocalParams({ ...localParams, watch_context: val })}
                    />
                  </div>
                </div>

                {/* Preferences */}
                <div>
                  <p className="text-xs uppercase tracking-wider text-chef-muted mb-3">Preferences</p>
                  <div className="flex flex-wrap gap-2">
                    <PreferenceChip
                      icon={Compass}
                      label="Adventurous"
                      active={localParams.feeling_adventurous}
                      onToggle={(val) => setLocalParams({ ...localParams, feeling_adventurous: val })}
                      activeColor="teal"
                      tooltip="Only new discoveries — nothing from your Diary or Watchlist."
                      testId="vibe-toggle-adventurous"
                    />
                    <PreferenceChip
                      icon={Tv}
                      label="My streaming"
                      active={localParams.only_my_streaming}
                      onToggle={(val) => setLocalParams({ ...localParams, only_my_streaming: val })}
                      activeColor="gold"
                      disabled={streamingCount === 0}
                      tooltip={streamingCount === 0
                        ? "Add services in Profile to enable filtering."
                        : "Filter to your selected streaming services."}
                      testId="vibe-toggle-streaming"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Apply button */}
            <div className="flex justify-center pt-1 pb-1">
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
