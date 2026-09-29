import React from 'react';
import { MOCK_DISEASES } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { TrendingUp, AlertTriangle, MapPin, Activity } from 'lucide-react';

export const DiseasePage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-500/10 text-orange-400 border border-orange-500/30">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Integrated Disease Surveillance Programme (IDSP)</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
          Disease Trend & Outbreak Surveillance
        </h2>
        <p className="text-xs text-slate-400">
          Early warning cluster detection for vector-borne, water-borne, and acute respiratory epidemics.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {MOCK_DISEASES.map((d) => (
          <Card key={d.disease} className="space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-sm text-slate-100">{d.disease}</h3>
                <span className="text-xs text-slate-400">Weekly Epidemiological Curve</span>
              </div>
              <Badge level={d.severity}>{d.severity.toUpperCase()} RISK</Badge>
            </div>

            <div className="flex items-baseline justify-between pt-1 font-mono">
              <div>
                <span className="text-2xl font-bold text-slate-100">
                  {d.cases_this_week.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400 ml-1.5">cases this week</span>
              </div>
              <span
                className={`text-xs font-bold ${
                  d.change_pct > 0 ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                {d.change_pct > 0 ? `+${d.change_pct}%` : `${d.change_pct}%`} vs last week
              </span>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">
                Active Hotspot Clusters:
              </span>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {d.hotspot_districts.map((h) => (
                  <span
                    key={h}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-800 text-[11px] text-slate-200"
                  >
                    <MapPin className="w-2.5 h-2.5 text-rose-400" />
                    {h}
                  </span>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default DiseasePage;
