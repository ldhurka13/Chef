import React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const EmergencyButton = ({ onClick }) => {
  return (
    <div className="flex justify-center -mt-8 relative z-10">
      <motion.button
        onClick={onClick}
        className="relative px-8 py-4 rounded-full 
                   bg-chef-gold/10 border border-chef-gold/30
                   backdrop-blur-xl shadow-glow-gold
                   group overflow-hidden"
        whileHover={{ scale: 1.05, y: -2 }}
        whileTap={{ scale: 0.98 }}
        data-testid="emergency-btn"
      >
        {/* Animated glow background */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-chef-gold/0 via-chef-gold/20 to-chef-gold/0"
          animate={{
            x: ["-100%", "100%"],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
          }}
        />
        
        <div className="relative flex items-center gap-3">
          <Sparkles 
            className="w-5 h-5 text-chef-gold transition-transform duration-300 
                       group-hover:rotate-12 group-hover:scale-110"
            strokeWidth={1.5}
          />
          <span className="font-serif text-lg text-chef-gold tracking-wide">
            I Can't Even
          </span>
          <Sparkles 
            className="w-5 h-5 text-chef-gold transition-transform duration-300 
                       group-hover:-rotate-12 group-hover:scale-110"
            strokeWidth={1.5}
          />
        </div>
      </motion.button>
    </div>
  );
};

export default EmergencyButton;
