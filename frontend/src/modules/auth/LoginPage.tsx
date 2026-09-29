import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useUIStore, UserRole } from '@/store/uiStore';
import { useToast } from '@/hooks/useToast';
import { useNavigate } from 'react-router-dom';
import { Activity, ShieldCheck, Lock, Mail, ArrowRight, KeyRound } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('officer@sanjeevani.gov.in');
  const [password, setPassword] = useState('••••••••••••');
  const [mfaCode, setMfaCode] = useState('');
  const [step, setStep] = useState<'credentials' | 'mfa'>('credentials');
  const { setActiveRole, activeRole } = useUIStore();
  const toast = useToast();
  const navigate = useNavigate();

  const presetRoles: { role: UserRole; title: string; email: string }[] = [
    { role: 'national_officer', title: 'National Health Officer', email: 'director.national@sanjeevani.gov.in' },
    { role: 'district_officer', title: 'District Collector / CMO', email: 'cmo.lucknow@sanjeevani.gov.in' },
    { role: 'facility_admin', title: 'Hospital Administrator', email: 'admin.patna@sanjeevani.gov.in' },
    { role: 'doctor', title: 'Chief Medical Officer', email: 'dr.verma@sanjeevani.gov.in' },
  ];

  const handleSelectPreset = (p: typeof presetRoles[0]) => {
    setActiveRole(p.role);
    setEmail(p.email);
    toast.info('Role Selected', `Configured credentials for ${p.title}`);
  };

  const handleCredentialsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('mfa');
    toast.info('MFA Challenge Sent', 'Multi-factor authentication code dispatched to secure authenticator.');
  };

  const handleMfaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Authentication Verified', `Welcome back, ${email}. Redirecting to Command Dashboard.`);
    setTimeout(() => {
      navigate('/');
    }, 600);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Branding header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Activity className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Sanjeevani Grid
          </h1>
          <p className="text-xs text-slate-400">
            Authorized Personnel Single Sign-On & Multi-Factor Gateway
          </p>
        </div>

        {/* Quick Role Preset Picker */}
        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-2">
          <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block text-center">
            Fast Role Preview (Testing Preset)
          </span>
          <div className="grid grid-cols-2 gap-1.5">
            {presetRoles.map((p) => (
              <button
                key={p.role}
                type="button"
                onClick={() => handleSelectPreset(p)}
                className={`p-2 rounded-xl text-left border text-[11px] transition-all ${
                  activeRole === p.role
                    ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300 font-semibold'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        {/* Login Card */}
        <Card className="p-6 bg-slate-900/90 border-slate-800 shadow-2xl">
          {step === 'credentials' ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Official Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Security Passcode
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2"
              >
                <span>Continue to MFA Verification</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit} className="space-y-4">
              <div className="text-center space-y-1 pb-1">
                <div className="p-2.5 rounded-full bg-cyan-500/10 text-cyan-400 inline-block mb-1">
                  <KeyRound className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-100">Enter Security Token</h3>
                <p className="text-[11px] text-slate-400">
                  Enter the 6-digit TOTP code generated by your authenticator.
                </p>
              </div>

              <div>
                <input
                  type="text"
                  maxLength={6}
                  placeholder="123456"
                  autoFocus
                  required
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl py-2.5 text-center text-lg font-mono tracking-widest text-emerald-400 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setStep('credentials')}
                  className="w-1/3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20"
                >
                  Verify & Enter Grid
                </button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
