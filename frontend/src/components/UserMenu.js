import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Settings, LogOut, ChevronDown } from "lucide-react";

const UserMenu = ({ user, onLogout, onProfileClick, onSettingsClick, onLoginClick, onSignupClick }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [hoveredItem, setHoveredItem] = useState(null);

  if (!user) {
    // Not logged in - show login/signup buttons with transparent design
    return (
      <div className="flex items-center gap-6">
        <button
          onClick={onLoginClick}
          onMouseEnter={() => setHoveredItem("login")}
          onMouseLeave={() => setHoveredItem(null)}
          className="relative text-sm font-medium tracking-wide py-2
                   text-chef-muted/60 hover:text-chef-platinum
                   transition-colors duration-300"
          data-testid="login-btn"
        >
          Log In
          {hoveredItem === "login" && (
            <motion.div
              layoutId="authUnderline"
              className="absolute -bottom-0 left-0 right-0 h-[2px] bg-chef-teal"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
        </button>
        <button
          onClick={onSignupClick}
          onMouseEnter={() => setHoveredItem("signup")}
          onMouseLeave={() => setHoveredItem(null)}
          className="relative text-sm font-medium tracking-wide py-2
                   text-chef-muted/60 hover:text-chef-platinum
                   transition-colors duration-300"
          data-testid="signup-btn"
        >
          Sign Up
          {hoveredItem === "signup" && (
            <motion.div
              layoutId="authUnderline"
              className="absolute -bottom-0 left-0 right-0 h-[2px] bg-chef-teal"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
        </button>
      </div>
    );
  }

  // Logged in - show user menu
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 py-2
                 text-chef-muted/60 hover:text-chef-platinum
                 transition-colors duration-300"
        data-testid="user-menu-btn"
      >
        {user.avatar_url ? (
          <img 
            src={user.avatar_url} 
            alt={user.username}
            className="w-7 h-7 rounded-full object-cover border border-white/20"
          />
        ) : (
          <div className="w-7 h-7 rounded-full border border-white/20
                        flex items-center justify-center">
            <User className="w-3.5 h-3.5" />
          </div>
        )}
        <span className="text-sm font-medium tracking-wide hidden md:block">
          {user.username}
        </span>
        <ChevronDown 
          className={`w-3.5 h-3.5 transition-transform duration-200
                     ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div 
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 w-48 z-50
                       bg-chef-surface/95 backdrop-blur-xl 
                       border border-white/10
                       shadow-cinematic overflow-hidden"
            >
              {/* User Info */}
              <div className="px-4 py-3 border-b border-white/10">
                <p className="text-sm text-chef-platinum font-medium truncate">
                  {user.username}
                </p>
                <p className="text-xs text-chef-muted truncate">
                  {user.email}
                </p>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    onProfileClick();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-chef-muted
                           hover:text-chef-platinum hover:bg-white/5 transition-colors"
                  data-testid="profile-menu-item"
                >
                  <User className="w-4 h-4" strokeWidth={1.5} />
                  Profile
                </button>
                <button
                  onClick={() => {
                    setIsOpen(false);
                    onSettingsClick();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-chef-muted
                           hover:text-chef-platinum hover:bg-white/5 transition-colors"
                  data-testid="settings-menu-item"
                >
                  <Settings className="w-4 h-4" strokeWidth={1.5} />
                  Settings
                </button>
              </div>

              {/* Logout */}
              <div className="py-1 border-t border-white/10">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    onLogout();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400
                           hover:text-red-300 hover:bg-red-500/10 transition-colors"
                  data-testid="logout-menu-item"
                >
                  <LogOut className="w-4 h-4" strokeWidth={1.5} />
                  Log Out
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UserMenu;
