'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Linkedin, Mail, Lock, Eye, EyeOff, CheckCircle2, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { LoadingButton } from '@/components/shared/LoadingButton';
import api from '@/lib/api';

type LoginState = 'idle' | 'checking' | 'logged_in' | 'form' | 'submitting' | 'running' | 'success' | 'error';

interface LinkedInLoginFormProps {
  onLoggedIn: () => void;
}

export function LinkedInLoginForm({ onLoggedIn }: LinkedInLoginFormProps) {
  const [state, setState] = useState<LoginState>('checking');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkSession = useCallback(async () => {
    try {
      const { data } = await api.get('/api/linkedin/session/status');
      if (data.logged_in) {
        setState('logged_in');
        onLoggedIn();
      } else {
        setState('form');
      }
    } catch {
      setState('form');
    }
  }, [onLoggedIn]);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get('/api/linkedin/session/login-status');
        if (!data.running && data.done) {
          stopPolling();
          if (data.success) {
            setState('success');
            setTimeout(() => {
              onLoggedIn();
            }, 1500);
          } else {
            setState('error');
            setError(data.error || 'Login failed. Check credentials or try cookie import.');
          }
        }
      } catch {
        stopPolling();
        setState('error');
        setError('Connection lost while checking login status.');
      }
    }, 2000);
  }, [stopPolling, onLoggedIn]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    setError('');
    setState('submitting');

    try {
      const { data } = await api.post('/api/linkedin/session/login', { email, password });
      if (data.success) {
        setState('running');
        startPolling();
      } else {
        setState('error');
        setError(data.message || 'Failed to start login.');
      }
    } catch (err: any) {
      setState('error');
      setError(err.response?.data?.detail || 'Failed to connect to server.');
    }
  };

  if (state === 'checking') {
    return (
      <div className="glass-card-premium rounded-2xl p-8 max-w-md mx-auto border-accent-cyan/10">
        <div className="flex flex-col items-center gap-4 py-8">
          <Loader2 className="w-8 h-8 text-accent-cyan animate-spin" />
          <p className="text-ice/50 text-sm">Checking LinkedIn session...</p>
        </div>
      </div>
    );
  }

  if (state === 'logged_in') {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card-premium rounded-2xl p-8 max-w-md mx-auto border-accent-cyan/10"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 flex items-center justify-center">
          <Linkedin className="w-5 h-5 text-accent-cyan" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-offwhite">LinkedIn Login</h3>
          <p className="text-xs text-ice/40">Sign in to enable LinkedIn lead search</p>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {state === 'running' && (
          <motion.div
            key="running"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4 py-6"
          >
            <div className="relative">
              <Loader2 className="w-10 h-10 text-accent-cyan animate-spin" />
              <div className="absolute inset-0 animate-ping rounded-full bg-accent-cyan/10" />
            </div>
            <p className="text-ice/70 text-sm text-center">
              Logging into LinkedIn in the background...
            </p>
            <p className="text-ice/40 text-xs text-center">
              This may take 30-60 seconds. We&apos;ll notify you when it&apos;s done.
            </p>
          </motion.div>
        )}

        {state === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-4 py-6"
          >
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>
            <p className="text-emerald-400 font-semibold">Logged in successfully!</p>
            <p className="text-ice/40 text-xs">Redirecting to search...</p>
          </motion.div>
        )}

        {(state === 'form' || state === 'submitting' || state === 'error') && (
          <motion.form
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onSubmit={handleLogin}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-ice/70 mb-2 flex items-center gap-2">
                <Mail className="w-4 h-4 text-accent-cyan" />
                Email
              </label>
              <div className="relative group">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  required
                  disabled={state === 'submitting'}
                  className="w-full px-4 py-3 rounded-xl border border-ocean/30 bg-navy/60 focus:bg-navy/80 focus:ring-2 focus:ring-accent-cyan/40 focus:border-accent-cyan/50 transition-all text-offwhite placeholder-ice/30 outline-none disabled:opacity-50"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-ice/70 mb-2 flex items-center gap-2">
                <Lock className="w-4 h-4 text-accent-cyan" />
                Password
              </label>
              <div className="relative group">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="LinkedIn password"
                  required
                  disabled={state === 'submitting'}
                  className="w-full px-4 py-3 pr-12 rounded-xl border border-ocean/30 bg-navy/60 focus:bg-navy/80 focus:ring-2 focus:ring-accent-cyan/40 focus:border-accent-cyan/50 transition-all text-offwhite placeholder-ice/30 outline-none disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ice/40 hover:text-ice/70 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-rose-500/10 p-3 rounded-xl border border-rose-500/30 flex items-start gap-2"
              >
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <p className="text-xs text-rose-300">{error}</p>
              </motion.div>
            )}

            <LoadingButton
              type="submit"
              isLoading={state === 'submitting'}
              variant="gradient-cyan"
              size="lg"
              fullWidth
              disabled={state === 'submitting' || !email.trim() || !password.trim()}
            >
              <Linkedin className="w-4 h-4" />
              Sign in with LinkedIn
            </LoadingButton>

            <div className="bg-accent-cyan/[0.04] p-3 rounded-xl border border-accent-cyan/10 flex items-start gap-2">
              <Sparkles className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
              <p className="text-[11px] text-ice/40 leading-relaxed">
                Your credentials are used only once to establish a session and are not stored.
              </p>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
