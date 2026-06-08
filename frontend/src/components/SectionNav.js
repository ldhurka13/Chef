import React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const sections = [
  { id: "chefs-curation", label: "Chef's Special", icon: Sparkles, isAI: true },
  { id: "explore", label: "Discover" },
  { id: "curated", label: "Your Bucketlist" },
  { id: "certified-swangy", label: "Trending Now" },
  { id: "all-time-classics", label: "All Time Classics" },
  { id: "marathon", label: "Marathon" },
];

const SectionNav = ({ activeSection, onSectionChange, hasVibeApplied }) => {
  return (
    <nav className="w-full mb-8" data-testid="section-nav">
      <div className="flex items-center gap-6 md:gap-10 overflow-x-auto pb-2 scrollbar-hide">
        {sections.map((section) => (
          <motion.button
            key={section.id}
            onClick={() => onSectionChange(section.id)}
            className={`relative whitespace-nowrap text-sm md:text-base font-medium tracking-wide
                       transition-colors duration-300 py-2 flex items-center gap-1.5
                       ${activeSection === section.id 
                         ? 'text-chef-platinum' 
                         : 'text-chef-muted/50 hover:text-chef-platinum'}`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            data-testid={`section-${section.id}`}
          >
            {section.icon && (
              <section.icon className={`w-4 h-4 ${hasVibeApplied && section.isAI ? 'text-purple-400' : ''}`} />
            )}
            {section.label}
            {section.isAI && hasVibeApplied && (
              <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/20 border border-purple-400/30 
                             rounded text-purple-400 ml-1">AI</span>
            )}
            
            {/* Active Underline */}
            {activeSection === section.id && (
              <motion.div
                layoutId="sectionUnderline"
                className={`absolute -bottom-0 left-0 right-0 h-[2px] 
                           ${section.isAI && hasVibeApplied ? 'bg-purple-400' : 'bg-chef-teal'}`}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
            )}
          </motion.button>
        ))}
      </div>
    </nav>
  );
};

export default SectionNav;
