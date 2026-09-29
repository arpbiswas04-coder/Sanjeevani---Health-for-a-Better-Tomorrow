import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useLocation } from 'react-router-dom';
import { Construction, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  phase: string;
  description: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  phase,
  description,
}) => {
  const location = useLocation();

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6 animate-in fade-in duration-200">
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-emerald-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Command Dashboard</span>
      </Link>

      <Card className="p-8 sm:p-12 text-center flex flex-col items-center justify-center border-dashed border-slate-700">
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-4">
          <Construction className="w-8 h-8 animate-bounce" />
        </div>

        <Badge level="info">{phase}</Badge>

        <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 mt-3">{title}</h2>
        <p className="mt-2 text-sm text-slate-400 max-w-md">{description}</p>

        <div className="mt-6 p-3 bg-slate-900/90 rounded-xl border border-slate-800 text-xs font-mono text-slate-400">
          Route: <span className="text-emerald-400">{location.pathname}</span>
        </div>
      </Card>
    </div>
  );
};
