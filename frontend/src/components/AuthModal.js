import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Lock, User, Calendar } from "lucide-react";

const AuthModal = ({ isOpen, onClose, mode, onModeChange, onLogin, onSignup, loading }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [birthYear, setBirthYear] = useState("1995");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (mode === "login") {
      const result = await onLogin(email, password);
      if (result?.error) {
        setError(result.error);
      }
    } else {
      if (password.length < 6) {
        setError("Password must be at least 6 characters");
        return;
      }
      const result = await onSignup(email, password, username, parseInt(birthYear));
      if (result?.error) {
        setError(result.error);
      }
    }
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setUsername("");
    setBirthYear("1995");
    setError("");
  };

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
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-md bg-flick-surface border border-white/10 
                     rounded-lg shadow-cinematic overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-flick-muted 
                       hover:text-flick-platinum transition-colors"
              data-testid="auth-close-btn"
            >
              <X className="w-5 h-5" strokeWidth={1.5} />
            </button>

            {/* Header */}
            <div className="px-8 pt-8 pb-6 text-center">
              <h2 className="font-serif text-2xl text-flick-platinum mb-2">
                {mode === "login" ? "Welcome Back" : "Join Flick"}
              </h2>
              <p className="text-sm text-flick-muted">
                {mode === "login" 
                  ? "Sign in to access your personalized recommendations" 
                  : "Create an account to save your preferences"}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="px-8 pb-8">
              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 
                              text-red-400 text-sm rounded">
                  {error}
                </div>
              )}

              {mode === "signup" && (
                <div className="mb-4">
                  <label className="block text-xs text-flick-muted uppercase tracking-wider mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-flick-muted" />
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      placeholder="Choose a username"
                      className="w-full pl-10 pr-4 py-3 bg-flick-bg border border-white/10 
                               text-flick-platinum placeholder-flick-muted/50
                               focus:border-flick-teal/50 focus:outline-none transition-colors"
                      data-testid="signup-username"
                    />
                  </div>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-xs text-flick-muted uppercase tracking-wider mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-flick-muted" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="your@email.com"
                    className="w-full pl-10 pr-4 py-3 bg-flick-bg border border-white/10 
                             text-flick-platinum placeholder-flick-muted/50
                             focus:border-flick-teal/50 focus:outline-none transition-colors"
                    data-testid="auth-email"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-xs text-flick-muted uppercase tracking-wider mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-flick-muted" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder={mode === "signup" ? "Min 6 characters" : "••••••••"}
                    className="w-full pl-10 pr-4 py-3 bg-flick-bg border border-white/10 
                             text-flick-platinum placeholder-flick-muted/50
                             focus:border-flick-teal/50 focus:outline-none transition-colors"
                    data-testid="auth-password"
                  />
                </div>
              </div>

              {mode === "signup" && (
                <div className="mb-6">
                  <label className="block text-xs text-flick-muted uppercase tracking-wider mb-2">
                    Birth Year (for nostalgia recommendations)
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-flick-muted" />
                    <input
                      type="number"
                      value={birthYear}
                      onChange={(e) => setBirthYear(e.target.value)}
                      min="1940"
                      max="2010"
                      className="w-full pl-10 pr-4 py-3 bg-flick-bg border border-white/10 
                               text-flick-platinum
                               focus:border-flick-teal/50 focus:outline-none transition-colors"
                      data-testid="signup-birthyear"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-flick-teal/20 border border-flick-teal/40
                         text-flick-teal font-medium
                         hover:bg-flick-teal/30 disabled:opacity-50
                         transition-colors duration-200"
                data-testid="auth-submit-btn"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-flick-teal border-t-transparent 
                                  rounded-full animate-spin" />
                    {mode === "login" ? "Signing in..." : "Creating account..."}
                  </span>
                ) : (
                  mode === "login" ? "Sign In" : "Create Account"
                )}
              </button>

              {/* Switch Mode */}
              <div className="mt-6 text-center">
                <span className="text-sm text-flick-muted">
                  {mode === "login" ? "Don't have an account?" : "Already have an account?"}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    resetForm();
                    onModeChange(mode === "login" ? "signup" : "login");
                  }}
                  className="ml-2 text-sm text-flick-teal hover:text-flick-platinum transition-colors"
                  data-testid="auth-switch-mode"
                >
                  {mode === "login" ? "Sign Up" : "Sign In"}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AuthModal;
