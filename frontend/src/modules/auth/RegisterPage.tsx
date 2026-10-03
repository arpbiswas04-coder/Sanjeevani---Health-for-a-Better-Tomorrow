import React from 'react';
import { Card } from '@/components/ui/Card';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Activity className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Personnel Registration
          </h1>
          <p className="text-xs text-slate-400">
            Join the Sanjeevani Grid federated healthcare logistics mesh
          </p>
        </div>

        <Card className="p-6 bg-slate-900/90 border-slate-800 shadow-2xl">
          <p role="status" className="text-xs text-amber-300">Self-registration is unavailable. Contact your administrator to provision an account.</p>
          <p className="text-sm text-slate-300">An administrator must provision your account and assign its roles and facility scope. This page does not collect or submit credentials.</p>
          <Link to="/login" className="text-emerald-400 text-xs font-semibold">Return to sign in</Link>

        </Card>
      </div>
    </div>
  );
};

export default RegisterPage;
