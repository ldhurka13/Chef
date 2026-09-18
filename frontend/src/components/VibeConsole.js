import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Smile, Zap, Loader2, User, Users, Heart, Compass, Tv, Info, Check, ChevronDown } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "./ui/tooltip";

const ComfortContextDropdown = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const options = [
    { id: "adventurous", label: "Surpise Me", icon: Compass },
    { id: "rewatch", label: "Re-Watch", icon: Tv },
    { id: "watchlist", label: "In Watchlist", icon: Tv },
  ];

  const selectedOption = options.find(opt => opt.id === value) || options[0];
  return (
    <div className="relative inline-block w-full max-w-[130px]">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full inline-flex items-center justify-between gap-3 h-11 min-h-[10px] px-4 rounded-lg
                   bg-chef-surface/60 border border-white/10 text-chef-platinum
                   hover:border-white/20 hover:bg-chef-surface/80
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-chef-teal/40
                   transition-all duration-200"
        data-testid="comfort-context-dropdown"
      >

        <div className="flex items-center gap-2.5">
          <span className="text-xs font-medium">{selectedOption.label}</span>
        </div>

        <ChevronDown
          className={`w-4 h-4 text-chef-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          strokeWidth={1.5}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 z-20
                         bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg
                         shadow-xl overflow-hidden"
            >
              {options.map(({ id, label }) => {
                const isSelected = value === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      onChange(id);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium
                               transition-colors
                               ${isSelected
                                 ? 'bg-chef-teal/15 text-chef-teal'
                                 : 'text-chef-platinum hover:bg-white/5'
                               }`}
                    data-testid={`comfort-context-option-${id}`}
                  >
                    <span className="flex-1 text-left">{label}</span>
                    {isSelected && <Check className="w-4 h-4" strokeWidth={2} />}
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

const StreamingContextDropdown = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const options = [
    { id: "all", label: "All"},
    { id: "mysubscriptions", label: "My Subscriptions"},
    { id: "rentorbuy", label: "Incl Rent/Buy"},
  ];

  const selectedOption = options.find(opt => opt.id === value) || options[0];

  return (
    <div className="relative inline-block w-full max-w-[130px]">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full inline-flex items-center justify-between gap-3 h-11 min-h-[10px] px-4 rounded-lg
                   bg-chef-surface/60 border border-white/10 text-chef-platinum
                   hover:border-white/20 hover:bg-chef-surface/80
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-chef-teal/40
                   transition-all duration-200"
        data-testid="streaming-context-dropdown"
      >

        <div className="flex items-center gap-2.5">
          <span className="text-xs font-medium">{selectedOption.label}</span>
        </div>

        <ChevronDown
          className={`w-4 h-4 text-chef-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          strokeWidth={1.5}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 z-20
                         bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg
                         shadow-xl overflow-hidden"
            >
              {options.map(({ id, label }) => {
                const isSelected = value === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      onChange(id);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium
                               transition-colors
                               ${isSelected
                                 ? 'bg-chef-teal/15 text-chef-teal'
                                 : 'text-chef-platinum hover:bg-white/5'
                               }`}
                    data-testid={`streaming-context-option-${id}`}
                  >
                    <span className="flex-1 text-left">{label}</span>
                    {isSelected && <Check className="w-4 h-4" strokeWidth={2} />}
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

// Watch Context Dropdown Component (compact segmented chips)
const WatchContextDropdown = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const options = [
    { id: "solo", label: "Solo", icon: User },
    { id: "date", label: "Date", icon: Heart },
    { id: "group", label: "Group", icon: Users },
  ];

  const selectedOption = options.find(opt => opt.id === value) || options[0];
  const SelectedIcon = selectedOption.icon;

  return (
    <div className="relative inline-block w-full max-w-[130px]">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full inline-flex items-center justify-between gap-3 h-11 min-h-[10px] px-4 rounded-lg
                   bg-chef-surface/60 border border-white/10 text-chef-platinum
                   hover:border-white/20 hover:bg-chef-surface/80
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-chef-teal/40
                   transition-all duration-200"
        data-testid="watch-context-dropdown"
      >

        <div className="flex items-center gap-2.5">
          <SelectedIcon className="w-4 h-4 text-chef-teal" strokeWidth={1.5} />
          <span className="text-xs font-medium">{selectedOption.label}</span>
        </div>

        <ChevronDown
          className={`w-4 h-4 text-chef-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          strokeWidth={1.5}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 z-20
                         bg-chef-surface/95 backdrop-blur-xl border border-white/10 rounded-lg
                         shadow-xl overflow-hidden"
            >
              {options.map(({ id, label, icon: Icon }) => {
                const isSelected = value === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      onChange(id);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium
                               transition-colors
                               ${isSelected
                                 ? 'bg-chef-teal/15 text-chef-teal'
                                 : 'text-chef-platinum hover:bg-white/5'
                               }`}
                    data-testid={`watch-context-option-${id}`}
                  >

                    <Icon className="w-4 h-4" strokeWidth={1.5} />
                    <span className="flex-1 text-left">{label}</span>
                    {isSelected && <Check className="w-4 h-4" strokeWidth={2} />}
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

const VerticalSlider = ({ steps, value, onChange, label, icon: Icon, color }) => {
  const getCurrentStep = () => {
    for (let i = 0; i < steps.length; i++) {
      if (value <= steps[i].max) {
        return steps[i];
      }
    }
    return steps[steps.length - 1];
  };
  const currentStep = getCurrentStep();

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Icon */}
      <div className={`p-3 rounded-full bg-white/5 ${color}`}>
        <Icon className="w-6 h-6" strokeWidth={1.5} />
      </div>

      {/* Label */}
      <span className="text-sm font-medium text-chef-muted/80">{label}</span>
    
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
      
      <motion.div
          key={currentStep.label}
          initial={{ opacity: 0, x: 3 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
          className="min-w-[90px] whitespace-nowrap justify-center text-xs font-medium text-chef-muted"
        >
          {currentStep.label}
      </motion.div>
      
      {/* Value Display */}
      <span className="text-xl font-serif text-chef-platinum">{value}</span>
    </div>
  );
};

const VibeConsole = ({ open, onOpenChange, params, onParamsChange, user }) => {
  const [localParams, setLocalParams] = useState({
    ...params,
    watch_context: params.watch_context || "solo",
    comfort_context: params.comfort_context || "adventurous",
    stream_context: params.stream_context || "all",
  });
  const [applyLoading, setApplyLoading] = useState(false);
  
  useEffect(() => {
    // Reset toggles to OFF each time the console opens, keep vibe sliders/context
    if (open) {
      setLocalParams({
        ...params,
        watch_context: params.watch_context || "solo",
        comfort_context: params.comfort_context || "adventurous",
        stream_context: params.stream_context || "all",
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
  
  const brainPowerSteps = [
    { max: 20, label: "Brain Dead" },
    { max: 40, label: "Zoned Out" },
    { max: 60, label: "System Rebooting" },
    { max: 80, label: "Locking In" },
    { max: 100, label: "Intellectual stimulation" }
  ];
 
  const moodSteps = [
    { max: 20, label: "Clown Behavior" },
    { max: 40, label: "Playful Banter" },
    { max: 60, label: "Happy Medium" },
    { max: 80, label: "Emotionally charged" },
    { max: 100, label: "Wanna feel something" }
  ];
 
  const energySteps = [
    { max: 20, label: "Sleep Mode" },
    { max: 40, label: "Battery Low" },
    { max: 60, label: "Waking Up" },
    { max: 80, label: "Let's get it" },
    { max: 100, label: "High Stakes" }
  ];

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
                color="text-chef-teal"
                steps={brainPowerSteps}
              />
              
              <VerticalSlider
                value={localParams.mood}
                onChange={(val) => setLocalParams({ ...localParams, mood: val })}
                label="Emotion"
                icon={Smile}
                color="text-chef-gold"
                steps={moodSteps}
              />
              
              <VerticalSlider
                value={localParams.energy}
                onChange={(val) => setLocalParams({ ...localParams, energy: val })}
                label="Energy"
                icon={Zap}
                color="text-chef-orange"
                steps={energySteps}
              />
            </div>

            {/* Divider */}
            <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-8" />
 
            {/* Configuration Section */}
            <div className="space-y-6 px-2">
              {/* Preferences */}
              <div className="flex items-start justify-center gap-6">
                <div role="radiogroup" aria-label="Watch context">
                  <WatchContextDropdown
                    value={localParams.watch_context}
                    onChange={(val) => setLocalParams({ ...localParams, watch_context: val })}
                  />
                </div>
                <div role="radiogroup" aria-label="Stream context">
                  <StreamingContextDropdown
                    value={localParams.stream_context}
                    onChange={(val) => setLocalParams({ ...localParams, stream_context: val })}
                  />
                </div>
                <div role="radiogroup" aria-label="Comfort context">
                  <ComfortContextDropdown
                    value={localParams.comfort_context}
                    onChange={(val) => setLocalParams({ ...localParams, comfort_context: val })}
                  />
                </div>
              </div>
            </div>
            
            <div className="flex justify-center mt-12 pb-1">
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