import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
import {
  ShieldCheck,
  Smartphone,
  KeyRound,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export const MFAPage: React.FC = () => {
  const [digits, setDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [backupCode, setBackupCode] = useState('');
  const [countdown, setCountdown] = useState(45);
  const [isVerifying, setIsVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const { user, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleDigitChange = (index: number, val: string) => {
    setErrorMsg(null);
    const cleaned = val.replace(/\D/g, '');
    const newDigits = [...digits];

    if (cleaned.length > 1) {
      // Handle paste
      const pasted = cleaned.slice(0, 6).split('');
      for (let i = 0; i < 6; i++) {
        newDigits[i] = pasted[i] || '';
      }
      setDigits(newDigits);
      const nextIndex = Math.min(pasted.length, 5);
      inputRefs.current[nextIndex]?.focus();
      return;
    }

    newDigits[index] = cleaned;
    setDigits(newDigits);

    if (cleaned && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    setErrorMsg(null);

    const code = useBackupCode ? backupCode.trim() : digits.join('');

    if (!useBackupCode && code.length !== 6) {
      setErrorMsg('Please enter all 6 digits of your authenticator code.');
      setIsVerifying(false);
      return;
    }

    if (useBackupCode && code.length < 8) {
      setErrorMsg('Please enter a valid backup recovery key.');
      setIsVerifying(false);
      return;
    }

    setTimeout(() => {
      setIsVerifying(false);
      // Demo acceptance: accept any 6 digits or 123456
      if (code === '000000') {
        setErrorMsg('Invalid code. Please check your authenticator app and try again.');
        toast.error('MFA Verification Failed', 'The code provided is incorrect or has expired.');
        return;
      }

      toast.success(
        'Identity Verified',
        'Multi-factor authentication confirmed. Initializing command session.'
      );
      const redirectTarget = location.state?.from || '/';
      navigate(redirectTarget, { replace: true });
    }, 900);
  };

  const handleResend = () => {
    if (countdown > 0) return;
    setCountdown(60);
    toast.info('New OTP Dispatched', 'A fresh 6-digit code was sent to your registered security device.');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full space-y-6 relative z-10 animate-in fade-in duration-300">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-2 shadow-lg shadow-emerald-500/10">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight">
            Two-Factor Verification
          </h1>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Defense-grade verification required for access to the National Health Resource Intelligence Grid.
          </p>
        </div>

        <Card className="p-6 sm:p-8 bg-slate-900/90 border-slate-800 shadow-2xl backdrop-blur-xl">
          <form onSubmit={handleVerify} className="space-y-6">
            {!useBackupCode ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Smartphone className="w-4 h-4 text-emerald-400" />
                    Enter 6-Digit Authenticator Code
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">TOTP / SMS</span>
                </div>

                {/* 6 Digit Input Boxes */}
                <div className="flex justify-between gap-2">
                  {digits.map((digit, i) => (
                    <input
                      key={i}
                      ref={(el) => (inputRefs.current[i] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleDigitChange(i, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(i, e)}
                      autoFocus={i === 0}
                      className="w-12 h-14 text-center text-xl font-bold font-mono bg-slate-950/80 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                    />
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={countdown > 0}
                    className={`text-[11px] font-medium transition-colors ${
                      countdown > 0
                        ? 'text-slate-500 cursor-not-allowed'
                        : 'text-emerald-400 hover:text-emerald-300 hover:underline'
                    }`}
                  >
                    {countdown > 0 ? `Resend code in ${countdown}s` : 'Resend Code via SMS'}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setUseBackupCode(true);
                      setErrorMsg(null);
                    }}
                    className="text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Use emergency recovery key
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span className="flex items-center gap-1.5 font-medium">
                    <KeyRound className="w-4 h-4 text-amber-400" />
                    Emergency Recovery Key
                  </span>
                </div>

                <input
                  type="text"
                  placeholder="e.g. SANJ-XXXX-XXXX-XXXX"
                  value={backupCode}
                  onChange={(e) => {
                    setBackupCode(e.target.value.toUpperCase());
                    setErrorMsg(null);
                  }}
                  autoFocus
                  className="w-full py-3 px-4 bg-slate-950 border border-slate-700 rounded-xl text-sm font-mono text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-500"
                />

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setUseBackupCode(false);
                      setErrorMsg(null);
                    }}
                    className="text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Switch back to authenticator app
                  </button>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-2 text-rose-300 text-xs">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isVerifying}
              className="w-full py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              {isVerifying ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Token...</span>
                </>
              ) : (
                <>
                  <span>Verify Identity & Proceed</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-800/80 text-center">
            <Link
              to="/login"
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              Back to Passcode Login
            </Link>
          </div>
        </Card>

        {/* Demo Helper Info */}
        <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-[11px] text-slate-400 text-center">
          <span className="text-emerald-400 font-semibold">Demo Hint:</span> Any 6-digit code (e.g.{' '}
          <strong className="text-slate-200 font-mono">123456</strong>) will successfully pass MFA verification.
        </div>
      </div>
    </div>
  );
};

export default MFAPage;
