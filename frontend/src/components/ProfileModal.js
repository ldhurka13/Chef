import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, User, Calendar, Film, Star } from "lucide-react";

const ProfileModal = ({ isOpen, onClose, user, watchHistory, onUpdateProfile }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [username, setUsername] = useState(user?.username || "");
  const [birthYear, setBirthYear] = useState(user?.birth_year || 1995);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setBirthYear(user.birth_year || 1995);
    }
  }, [user]);

  const handleSave = async () => {
    await onUpdateProfile({ username, birth_year: birthYear });
    setIsEditing(false);
  };

  // Calculate stats
  const totalWatched = watchHistory?.length || 0;
  const avgRating = watchHistory?.length 
    ? (watchHistory.reduce((sum, m) => sum + (m.user_rating || 0), 0) / watchHistory.length).toFixed(1)
    : "0";

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[80] flex items-center justify-center p-4"
          onClick={onClose}
        >
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-lg bg-chef-surface border border-white/10 
                     rounded-lg shadow-cinematic overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-chef-muted 
                       hover:text-chef-platinum transition-colors"
            >
              <X className="w-5 h-5" strokeWidth={1.5} />
            </button>

            {/* Header */}
            <div className="px-8 pt-8 pb-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-chef-teal/20 border border-chef-teal/30
                              flex items-center justify-center">
                  <User className="w-8 h-8 text-chef-teal" />
                </div>
                <div>
                  <h2 className="font-serif text-2xl text-chef-platinum">
                    {user?.username || "User"}
                  </h2>
                  <p className="text-sm text-chef-muted">{user?.email}</p>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="px-8 pb-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-chef-bg/50 rounded-lg border border-white/5">
                  <Film className="w-5 h-5 text-chef-teal mx-auto mb-2" />
                  <p className="text-2xl font-serif text-chef-platinum">{totalWatched}</p>
                  <p className="text-xs text-chef-muted">Movies Watched</p>
                </div>
                <div className="text-center p-4 bg-chef-bg/50 rounded-lg border border-white/5">
                  <Star className="w-5 h-5 text-chef-gold mx-auto mb-2" />
                  <p className="text-2xl font-serif text-chef-platinum">{avgRating}</p>
                  <p className="text-xs text-chef-muted">Avg Rating</p>
                </div>
                <div className="text-center p-4 bg-chef-bg/50 rounded-lg border border-white/5">
                  <Calendar className="w-5 h-5 text-chef-orange mx-auto mb-2" />
                  <p className="text-2xl font-serif text-chef-platinum">{user?.birth_year || "-"}</p>
                  <p className="text-xs text-chef-muted">Birth Year</p>
                </div>
              </div>
            </div>

            {/* Edit Form */}
            <div className="px-8 pb-8">
              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                      Username
                    </label>
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-4 py-3 bg-chef-bg border border-white/10 
                               text-chef-platinum
                               focus:border-chef-teal/50 focus:outline-none transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                      Birth Year
                    </label>
                    <input
                      type="number"
                      value={birthYear}
                      onChange={(e) => setBirthYear(parseInt(e.target.value))}
                      min="1940"
                      max="2010"
                      className="w-full px-4 py-3 bg-chef-bg border border-white/10 
                               text-chef-platinum
                               focus:border-chef-teal/50 focus:outline-none transition-colors"
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="flex-1 py-2 border border-white/10 text-chef-muted
                               hover:text-chef-platinum transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSave}
                      className="flex-1 py-2 bg-chef-teal/20 border border-chef-teal/30
                               text-chef-teal hover:bg-chef-teal/30 transition-colors"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="w-full py-3 border border-white/10 text-chef-muted
                           hover:text-chef-platinum hover:border-white/20 transition-colors"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ProfileModal;
