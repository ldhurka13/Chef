import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Lock, User, Calendar, ArrowLeft, Loader2 } from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthModal = ({ isOpen, onClose, mode, onModeChange, onLogin, onSignup, loading }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [error, setError] = useState("");
  const [view, setView] = useState("form"); // "form" | "forgot"
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);

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
      const birthYear = birthDate ? new Date(birthDate).getFullYear() : 1995;
      const result = await onSignup(email, password, username, birthYear, birthDate);
      if (result?.error) {
        setError(result.error);
      }
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setError("");
    setForgotLoading(true);
    try {
      const res = await axios.post(`${API}/auth/forgot-password`, { email: forgotEmail });
      if (res.data.reset_url) {
        // Email couldn't be sent — redirect directly to reset page
        window.location.href = res.data.reset_url;
      } else {
        setForgotSent(true);
        toast.success("Reset link sent to your email");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send reset email");
    } finally {
      setForgotLoading(false);
    }
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setUsername("");
    setBirthDate("");
    setError("");
    setView("form");
    setForgotEmail("");
    setForgotSent(false);
  };

  const switchToForgot = () => {
    setError("");
    setForgotEmail(email);
    setForgotSent(false);
    setView("forgot");
  };

  const switchBackToLogin = () => {
    setError("");
    setView("form");
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
          <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3 }}
            className="relative w-full max-w-md bg-chef-surface border border-white/10 
                     shadow-cinematic overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 text-chef-muted 
                       hover:text-chef-platinum transition-colors"
              data-testid="auth-close-btn"
            >
              <X className="w-5 h-5" strokeWidth={1.5} />
            </button>

            {view === "forgot" ? (
              /* Forgot Password View */
              <div className="px-8 py-8">
                <button
                  onClick={switchBackToLogin}
                  className="flex items-center gap-1.5 text-sm text-chef-muted hover:text-chef-platinum
                           transition-colors mb-6"
                  data-testid="forgot-back-btn"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Sign In
                </button>

                <h2 className="font-serif text-2xl text-chef-platinum mb-2">
                  {forgotSent ? "Check your email" : "Forgot password?"}
                </h2>
                <p className="text-sm text-chef-muted mb-6">
                  {forgotSent
                    ? "We've sent a password reset link to your email. Check your inbox and follow the link to reset your password."
                    : "Enter the email associated with your account and we'll send you a reset link."}
                </p>

                {!forgotSent ? (
                  <form onSubmit={handleForgotPassword}>
                    {error && (
                      <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 
                                    text-red-400 text-sm" data-testid="forgot-error">
                        {error}
                      </div>
                    )}
                    <div className="mb-6">
                      <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                        Email
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                        <input
                          type="email"
                          value={forgotEmail}
                          onChange={(e) => setForgotEmail(e.target.value)}
                          required
                          placeholder="your@email.com"
                          className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                                   text-chef-platinum placeholder-chef-muted/50
                                   focus:border-chef-teal/50 focus:outline-none transition-colors"
                          data-testid="forgot-email"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      disabled={forgotLoading}
                      className="w-full py-3 bg-chef-teal/20 border border-chef-teal/40
                               text-chef-teal font-medium
                               hover:bg-chef-teal/30 disabled:opacity-50
                               transition-colors duration-200"
                      data-testid="forgot-submit-btn"
                    >
                      {forgotLoading ? (
                        <span className="flex items-center justify-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Sending...
                        </span>
                      ) : (
                        "Send Reset Link"
                      )}
                    </button>
                  </form>
                ) : (
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-full bg-chef-teal/10 border border-chef-teal/20
                                  flex items-center justify-center mx-auto mb-4">
                      <Mail className="w-7 h-7 text-chef-teal" />
                    </div>
                    <p className="text-xs text-chef-muted/60 mt-4">
                      Didn't receive it? Check your spam folder or{" "}
                      <button
                        onClick={() => setForgotSent(false)}
                        className="text-chef-teal hover:underline"
                        data-testid="forgot-resend-btn"
                      >
                        try again
                      </button>
                    </p>
                  </div>
                )}
              </div>
            ) : (
              /* Login / Signup View */
              <>
                <div className="px-8 pt-8 pb-6 text-center">
                  <h2 className="font-serif text-2xl text-chef-platinum mb-2">
                    {mode === "login" ? "Welcome Back" : "Join Chef"}
                  </h2>
                  <p className="text-sm text-chef-muted">
                    {mode === "login" 
                      ? "Sign in to access your personalized recommendations" 
                      : "Create an account to save your preferences"}
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="px-8 pb-8">
                  {error && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 
                                  text-red-400 text-sm" data-testid="auth-error">
                      {error}
                    </div>
                  )}

                  {mode === "signup" && (
                    <div className="mb-4">
                      <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                        Username
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                        <input
                          type="text"
                          value={username}
                          onChange={(e) => setUsername(e.target.value)}
                          required
                          placeholder="Choose a username"
                          className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                                   text-chef-platinum placeholder-chef-muted/50
                                   focus:border-chef-teal/50 focus:outline-none transition-colors"
                          data-testid="signup-username"
                        />
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                      Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        placeholder="your@email.com"
                        className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                                 text-chef-platinum placeholder-chef-muted/50
                                 focus:border-chef-teal/50 focus:outline-none transition-colors"
                        data-testid="auth-email"
                      />
                    </div>
                  </div>

                  <div className={mode === "signup" ? "mb-4" : "mb-2"}>
                    <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                      Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        placeholder={mode === "signup" ? "Min 6 characters" : "••••••••"}
                        className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                                 text-chef-platinum placeholder-chef-muted/50
                                 focus:border-chef-teal/50 focus:outline-none transition-colors"
                        data-testid="auth-password"
                      />
                    </div>
                  </div>

                  {mode === "login" && (
                    <div className="mb-6 text-right">
                      <button
                        type="button"
                        onClick={switchToForgot}
                        className="text-xs text-chef-muted hover:text-chef-teal transition-colors"
                        data-testid="forgot-password-link"
                      >
                        Forgot password?
                      </button>
                    </div>
                  )}

                  {mode === "signup" && (
                    <div className="mb-6">
                      <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                        Birth Date
                      </label>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                        <input
                          type="date"
                          value={birthDate}
                          onChange={(e) => setBirthDate(e.target.value)}
                          max={new Date().toISOString().split('T')[0]}
                          className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                                   text-chef-platinum
                                   focus:border-chef-teal/50 focus:outline-none transition-colors
                                   [color-scheme:dark]"
                          data-testid="signup-birthdate"
                        />
                      </div>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-chef-teal/20 border border-chef-teal/40
                             text-chef-teal font-medium
                             hover:bg-chef-teal/30 disabled:opacity-50
                             transition-colors duration-200"
                    data-testid="auth-submit-btn"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-chef-teal border-t-transparent 
                                      rounded-full animate-spin" />
                        {mode === "login" ? "Signing in..." : "Creating account..."}
                      </span>
                    ) : (
                      mode === "login" ? "Sign In" : "Create Account"
                    )}
                  </button>

                  <div className="mt-6 text-center">
                    <span className="text-sm text-chef-muted">
                      {mode === "login" ? "Don't have an account?" : "Already have an account?"}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        resetForm();
                        onModeChange(mode === "login" ? "signup" : "login");
                      }}
                      className="ml-2 text-sm text-chef-teal hover:text-chef-platinum transition-colors"
                      data-testid="auth-switch-mode"
                    >
                      {mode === "login" ? "Sign Up" : "Sign In"}
                    </button>
                  </div>
                </form>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AuthModal;
