import React from "react";
import { motion } from "framer-motion";

const sections = [
  { id: "curated", label: "Curated For You" },
  { id: "chefs-special", label: "Chef's Special" },
  { id: "certified-swangy", label: "Certified Swangy" },
  { id: "all-time-classics", label: "All Time Classics" },
  { id: "explore", label: "Explore" },
  { id: "marathon", label: "Marathon" },
];

const SectionNav = ({ activeSection, onSectionChange }) => {
  return (
    <nav className="w-full mb-8" data-testid="section-nav">
      <div className="flex items-center gap-6 md:gap-10 overflow-x-auto pb-2 scrollbar-hide">
        {sections.map((section) => (
          <motion.button
            key={section.id}
            onClick={() => onSectionChange(section.id)}
            className={`relative whitespace-nowrap text-sm md:text-base font-medium tracking-wide
                       transition-colors duration-300 py-2
                       ${activeSection === section.id 
                         ? 'text-chef-platinum' 
                         : 'text-chef-muted/50 hover:text-chef-platinum'}`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            data-testid={`section-${section.id}`}
          >
            {section.label}
            
            {/* Active Underline */}
            {activeSection === section.id && (
              <motion.div
                layoutId="sectionUnderline"
                className="absolute -bottom-0 left-0 right-0 h-[2px] bg-chef-teal"
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
