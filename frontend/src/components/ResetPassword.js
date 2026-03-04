import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Lock, Check, Loader2 } from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: password,
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reset password");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <h2 className="font-serif text-2xl text-chef-platinum mb-2">Invalid Reset Link</h2>
          <p className="text-sm text-chef-muted mb-6">This link is missing or malformed.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2.5 rounded-full bg-chef-teal/10 border border-chef-teal/20
                     text-chef-teal text-sm hover:bg-chef-teal/20 transition-colors"
          >
            Go Home
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-chef-surface border border-white/10 shadow-cinematic"
      >
        <div className="px-8 py-8">
          {success ? (
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-chef-teal/10 border border-chef-teal/20
                            flex items-center justify-center mx-auto mb-4">
                <Check className="w-7 h-7 text-chef-teal" />
              </div>
              <h2 className="font-serif text-2xl text-chef-platinum mb-2">Password Reset</h2>
              <p className="text-sm text-chef-muted mb-6">
                Your password has been updated successfully. You can now sign in.
              </p>
              <button
                onClick={() => navigate("/")}
                className="w-full py-3 bg-chef-teal/20 border border-chef-teal/40
                         text-chef-teal font-medium hover:bg-chef-teal/30 transition-colors"
                data-testid="reset-go-home-btn"
              >
                Go to Sign In
              </button>
            </div>
          ) : (
            <>
              <h2 className="font-serif text-2xl text-chef-platinum mb-2">Set new password</h2>
              <p className="text-sm text-chef-muted mb-6">
                Enter your new password below.
              </p>
              <form onSubmit={handleSubmit}>
                {error && (
                  <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 
                                text-red-400 text-sm" data-testid="reset-error">
                    {error}
                  </div>
                )}
                <div className="mb-4">
                  <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      placeholder="Min 6 characters"
                      className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                               text-chef-platinum placeholder-chef-muted/50
                               focus:border-chef-teal/50 focus:outline-none transition-colors"
                      data-testid="reset-password"
                    />
                  </div>
                </div>
                <div className="mb-6">
                  <label className="block text-xs text-chef-muted uppercase tracking-wider mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-chef-muted" />
                    <input
                      type="password"
                      value={confirm}
                      onChange={(e) => setConfirm(e.target.value)}
                      required
                      placeholder="Re-enter password"
                      className="w-full pl-10 pr-4 py-3 bg-chef-bg border border-white/10 
                               text-chef-platinum placeholder-chef-muted/50
                               focus:border-chef-teal/50 focus:outline-none transition-colors"
                      data-testid="reset-confirm-password"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-chef-teal/20 border border-chef-teal/40
                           text-chef-teal font-medium
                           hover:bg-chef-teal/30 disabled:opacity-50
                           transition-colors duration-200"
                  data-testid="reset-submit-btn"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Resetting...
                    </span>
                  ) : (
                    "Reset Password"
                  )}
                </button>
              </form>
            </>
          )}
        </div>
      </motion.div>
    </main>
  );
};

export default ResetPassword;
