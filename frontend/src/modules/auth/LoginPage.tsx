import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
import { useNavigate, useLocation } from 'react-router-dom';
import { Role, ROLE_LABELS } from '@/types/auth';
import { DEMO_ACCOUNTS } from '@/services/authService';
import {
  Activity,
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  Eye,
  EyeOff,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('national.command@sanjeevani.gov.in');
  const [password, setPassword] = useState('NationalPass2026!');
  const [selectedRole, setSelectedRole] = useState<Role | ''>('NATIONAL_ADMIN');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSubmitted, setForgotSubmitted] = useState(false);

  const { login, isLoading, error, clearError } = useAuthStore();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSelectDemoPreset = (roleKey: Role) => {
    const demo = DEMO_ACCOUNTS[roleKey];
    setSelectedRole(roleKey);
    setEmail(demo.email);
    setPassword(demo.pass);
    clearError();
    toast.info('Role Preset Applied', `Loaded credentials for ${ROLE_LABELS[roleKey]}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!selectedRole) {
      toast.warning('Role Selection Required', 'Please select your authorized role before logging in.');
      return;
    }

    try {
      const redirectRoute = await login({
        email,
        password,
        role: selectedRole,
        rememberMe,
      });

      toast.success(
        'Authentication Successful',
        `Welcome to Sanjeevani Grid. Initializing ${ROLE_LABELS[selectedRole]} session.`
      );

      // Check if there was an attempted URL redirected from
      const destination = location.state?.from?.pathname || redirectRoute;
      navigate(destination, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      // Error is stored in authStore.error and displayed in the UI
      toast.error('Authentication Error', msg);
    }
  };

  const handleForgotPasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail) return;
    setForgotSubmitted(true);
    toast.info(
      'Recovery Dispatched',
      'If your account is registered with the Health Mesh, instructions have been sent.'
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-lg space-y-6">
        {/* Branding Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shadow-lg shadow-emerald-500/10">
            <Activity className="w-8 h-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            Sanjeevani Grid
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-sm mx-auto">
            Federated AI-Powered Smart Health & Supply Chain Resilience Platform
          </p>
        </div>

        {/* Quick Testing Role Presets Picker */}
        <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl space-y-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-400" />
              Fast Role Demo Presets
            </span>
            <span className="text-[10px] text-slate-500 font-mono">1-Click Autofill</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {(Object.keys(ROLE_LABELS) as Role[]).map((rKey) => (
              <button
                key={rKey}
                type="button"
                onClick={() => handleSelectDemoPreset(rKey)}
                className={`p-2 rounded-xl text-left border text-[11px] transition-all ${
                  selectedRole === rKey
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 font-semibold shadow-sm'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <div className="font-bold truncate">{ROLE_LABELS[rKey]}</div>
                <div className="text-[9px] font-mono text-slate-500">{rKey}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Login Card */}
        <Card className="p-6 sm:p-8 bg-slate-900/90 border-slate-800 shadow-2xl space-y-5">
          <div className="border-b border-slate-800/80 pb-3">
            <h2 className="text-base font-bold text-slate-100">Command Access Portal</h2>
            <p className="text-xs text-slate-400">National Health Resource Intelligence & Command Platform</p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              role="alert"
              className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2.5 animate-in fade-in"
            >
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <strong className="block font-bold">Authentication Refused</strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Role Selector (Task 1 Requirement) */}
            <div>
              <label
                htmlFor="role-select"
                className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5"
              >
                Role <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <select
                  id="role-select"
                  aria-label="Role"
                  value={selectedRole}
                  onChange={(e) => {
                    setSelectedRole(e.target.value as Role);
                    clearError();
                  }}
                  required
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 font-medium focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                >
                  <option value="" disabled>
                    -- Select your role ▼ --
                  </option>
                  {(Object.keys(ROLE_LABELS) as Role[]).map((rKey) => (
                    <option key={rKey} value={rKey}>
                      {ROLE_LABELS[rKey]} ({rKey})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Email / Username Input */}
            <div>
              <label
                htmlFor="email-input"
                className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5"
              >
                Official Email / Username <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  id="email-input"
                  aria-label="Official Email / Username"
                  type="email"
                  required
                  placeholder="officer@sanjeevani.gov.in"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    clearError();
                  }}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
              </div>
            </div>

            {/* Password Input with Show/Hide Toggle */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="password-input"
                  className="block text-xs font-bold uppercase tracking-wider text-slate-300"
                >
                  Passcode / Password <span className="text-rose-400">*</span>
                </label>
                <button
                  type="button"
                  onClick={() => setIsForgotModalOpen(true)}
                  className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
                >
                  Forgot passcode / Emergency access
                </button>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  id="password-input"
                  aria-label="Passcode / Password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    clearError();
                  }}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-10 pr-10 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="p-1 rounded text-slate-400 hover:text-slate-200 absolute right-3 top-2.5"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center gap-2 pt-1">
              <input
                id="remember-me"
                aria-label="Remember this terminal"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-0"
              />
              <label htmlFor="remember-me" className="text-xs text-slate-400 cursor-pointer select-none">
                Remember this terminal
              </label>
            </div>

            {/* Submit Button with Loading State */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-emerald-500/50 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Credentials & Permissions...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Command Portal</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Security Assurance Footer */}
          <div className="border-t border-slate-800/80 pt-4 flex items-center justify-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-400/80" />
            <span>Role-Based Zero-Trust Authorization • TLS 1.3 Encrypted</span>
          </div>
        </Card>
      </div>

      {/* Forgot Password Modal */}
      {isForgotModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-emerald-400" />
                Recover Authentication Passcode
              </h3>
              <button
                onClick={() => {
                  setIsForgotModalOpen(false);
                  setForgotSubmitted(false);
                }}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {!forgotSubmitted ? (
              <form onSubmit={handleForgotPasswordSubmit} className="space-y-4 text-xs">
                <p className="text-slate-400 leading-relaxed">
                  Enter your official email registered with the Ministry of Health or State Health Directorate.
                </p>
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Official Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="officer@sanjeevani.gov.in"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsForgotModalOpen(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold"
                  >
                    Send Token Reset
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3 text-center py-2 text-xs">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <h4 className="font-bold text-slate-100">Recovery Instructions Sent</h4>
                <p className="text-slate-400 text-[11px]">
                  Please verify your government inbox or contact your State Surveillance Directorate for cryptographic key reset.
                </p>
                <button
                  onClick={() => setIsForgotModalOpen(false)}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-bold mt-2"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
