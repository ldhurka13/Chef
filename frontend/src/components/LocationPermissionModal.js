import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Check } from "lucide-react";

const LocationPermissionModal = ({ isOpen, onSelect }) => {
  const options = [
    {
      id: "always",
      title: "Always",
      description: "Automatically use your location for better recommendations",
    },
    {
      id: "ask",
      title: "Ask Every Time",
      description: "We'll ask permission each time you log in",
    },
    {
      id: "never",
      title: "Never",
      description: "Don't use location data for recommendations",
    },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[90] flex items-center justify-center p-4"
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/95 backdrop-blur-sm" />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-md bg-chef-surface border border-white/10 
                     shadow-cinematic overflow-hidden"
          >
            {/* Header */}
            <div className="px-8 pt-8 pb-6 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-chef-teal/20 
                            border border-chef-teal/30 flex items-center justify-center">
                <MapPin className="w-8 h-8 text-chef-teal" />
              </div>
              <h2 className="font-serif text-2xl text-chef-platinum mb-2">
                Location Access
              </h2>
              <p className="text-sm text-chef-muted">
                Chef uses your location to provide weather-based recommendations
              </p>
            </div>

            {/* Options */}
            <div className="px-8 pb-8 space-y-3">
              {options.map((option) => (
                <button
                  key={option.id}
                  onClick={() => onSelect(option.id)}
                  className="w-full p-4 text-left bg-chef-bg/50 border border-white/5
                           hover:border-chef-teal/30 hover:bg-chef-teal/5
                           transition-all duration-200 group"
                  data-testid={`location-${option.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-chef-platinum font-medium">
                        {option.title}
                      </p>
                      <p className="text-xs text-chef-muted mt-1">
                        {option.description}
                      </p>
                    </div>
                    <div className="w-5 h-5 rounded-full border border-white/20 
                                  group-hover:border-chef-teal/50 group-hover:bg-chef-teal/20
                                  flex items-center justify-center transition-colors">
                      <Check className="w-3 h-3 text-chef-teal opacity-0 group-hover:opacity-100 
                                      transition-opacity" />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LocationPermissionModal;
