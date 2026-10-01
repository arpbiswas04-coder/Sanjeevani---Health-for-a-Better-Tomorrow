import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LogOut, Home } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { getRoleHomeRoute } from '@/app/roleRoutes';
import { ROLE_LABELS } from '@/types/auth';

export const UnauthorizedPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { role, user, logout } = useAuthStore();

  const attemptedUrl = location.state?.attemptedUrl || 'this protected resource';
  const roleTitle = role ? ROLE_LABELS[role] : 'Unassigned';
  const homeRoute = getRoleHomeRoute(role);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl text-center space-y-6">
        <div className="inline-flex p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <ShieldAlert className="w-12 h-12 animate-pulse" />
        </div>

        <div className="space-y-2">
          <span className="text-[11px] font-mono uppercase font-bold text-rose-400 tracking-wider">
            HTTP 403 • Insufficient Authorization
          </span>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">
            Restricted Jurisdiction Access
          </h1>
          <p className="text-xs text-slate-400 leading-relaxed">
            Your authenticated credentials do not possess security clearance to access{' '}
            <code className="text-rose-300 font-mono bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-500/20">
              {attemptedUrl}
            </code>
            .
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-left text-xs space-y-1.5">
          <div className="text-slate-400">
            Authenticated User: <strong className="text-slate-200">{user?.name || 'Session Active'}</strong>
          </div>
          <div className="text-slate-400">
            Assigned Tier: <span className="font-mono text-emerald-400 font-bold">{roleTitle}</span>
          </div>
          <div className="text-[11px] text-slate-500 pt-1">
            Access to cross-jurisdiction command tiers requires explicit elevation by the Ministry of Health or State Health Authority.
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <Link
            to={homeRoute}
            className="flex-1 py-2.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
          >
            <Home className="w-4 h-4" />
            Go to Your Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

export default UnauthorizedPage;
