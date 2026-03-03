import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, Sliders, Heart, Film } from "lucide-react";

const NavItem = ({ icon: Icon, label, isActive, onClick }) => {
  return (
    <motion.button
      onClick={onClick}
      className="relative flex flex-col items-center gap-1 group"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      <Icon 
        className={`w-5 h-5 transition-all duration-300 stroke-1
                   ${isActive 
                     ? 'text-flick-platinum' 
                     : 'text-flick-muted group-hover:text-flick-platinum'}`}
      />
      <span 
        className={`text-[10px] tracking-wider uppercase transition-all duration-300
                   ${isActive 
                     ? 'text-flick-platinum' 
                     : 'text-flick-muted/0 group-hover:text-flick-muted'}`}
      >
        {label}
      </span>
      
      {/* Active indicator */}
      {isActive && (
        <motion.div
          layoutId="navIndicator"
          className="absolute -bottom-2 w-1 h-1 bg-flick-teal rounded-full"
        />
      )}
    </motion.button>
  );
};

const FloatingNav = ({ onVibeClick, onEmergencyClick }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav 
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 
                 h-16 px-8 rounded-full 
                 bg-flick-surface/80 backdrop-blur-xl 
                 border border-white/10 
                 flex items-center gap-10
                 shadow-cinematic"
      data-testid="floating-nav"
    >
      <NavItem
        icon={Home}
        label="Home"
        isActive={location.pathname === "/"}
        onClick={() => navigate("/")}
      />
      
      <NavItem
        icon={Sliders}
        label="Vibe"
        isActive={false}
        onClick={onVibeClick}
      />
      
      {/* Emergency Button - Center Prominent */}
      <motion.button
        onClick={onEmergencyClick}
        className="relative -mt-4 w-14 h-14 rounded-full 
                   bg-flick-gold/20 border border-flick-gold/30
                   flex items-center justify-center
                   shadow-glow-gold animate-pulse-glow
                   hover:bg-flick-gold/30 hover:border-flick-gold/50
                   transition-all duration-300"
        whileHover={{ scale: 1.1, y: -2 }}
        whileTap={{ scale: 0.95 }}
        data-testid="nav-emergency-btn"
      >
        <Heart className="w-6 h-6 text-flick-gold stroke-1" />
      </motion.button>
      
      <NavItem
        icon={Film}
        label="History"
        isActive={location.pathname === "/history"}
        onClick={() => navigate("/history")}
      />
      
      <NavItem
        icon={Heart}
        label="Comfort"
        isActive={false}
        onClick={onEmergencyClick}
      />
    </nav>
  );
};

export default FloatingNav;
