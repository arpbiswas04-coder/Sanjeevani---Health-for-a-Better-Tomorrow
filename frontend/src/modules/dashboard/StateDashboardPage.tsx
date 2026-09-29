import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/store/authStore';
import { Link } from 'react-router-dom';
import {
  Building2,
  Package,
  Bed,
  TrendingUp,
  Map,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Activity,
  Layers,
} from 'lucide-react';
import { MOCK_FACILITIES } from '@/services/mockData';

export const StateDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const assignedState = user?.state || 'Uttar Pradesh';

  // Scope facilities to authenticated state
  const stateFacilities = MOCK_FACILITIES.filter(
    (f) => f.state.toLowerCase() === assignedState.toLowerCase()
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Scope Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>State Health Command Jurisdiction</span>
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight mt-1 flex items-center gap-2">
            {assignedState} State Command Hub
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
              STATE_ADMIN
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Sub-divisional district aggregation, state-level buffer inventories, and emergency surge coordination.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/state/map"
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-colors shadow-sm shadow-emerald-500/20"
          >
            <Map className="w-4 h-4" />
            State Live Map
          </Link>
          <Link
            to="/state/emergency"
            className="flex items-center gap-1.5 px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-xl text-xs font-bold transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            Surge Protocol
          </Link>
        </div>
      </div>

      {/* State-Scoped KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>State Health Facilities</span>
            <Building2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">
            {stateFacilities.length > 0 ? stateFacilities.length * 32 : 194}
          </div>
          <div className="text-[11px] text-emerald-400 flex items-center gap-1">
            <span>98.2% Telemetry Online</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Bed Occupancy</span>
            <Bed className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">81.4%</div>
          <div className="text-[11px] text-amber-400 flex items-center gap-1">
            <span>Elevated in 3 Districts</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>State Medicine Cover</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">18.4 Days</div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <span>Central depot buffer normal</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>State Disease Trends</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">R0 = 1.28</div>
          <div className="text-[11px] text-teal-400 flex items-center gap-1">
            <span>Dengue Surveillance Active</span>
          </div>
        </Card>
      </div>

      {/* Districts under Jurisdiction */}
      <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100">
              Districts Under {assignedState} Health Authority
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            Authorized Scope: <strong className="text-slate-200">Strictly State Boundaries</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { name: 'Lucknow District', facilities: 28, beds: '88% Occ', status: 'High', alert: 'Insulin stock warning' },
            { name: 'Varanasi District', facilities: 21, beds: '74% Occ', status: 'Moderate', alert: 'Staff rotation normal' },
            { name: 'Gorakhpur District', facilities: 19, beds: '82% Occ', status: 'High', alert: 'Encephalitis cluster watch' },
            { name: 'Kanpur Nagar', facilities: 32, beds: '79% Occ', status: 'Moderate', alert: 'Central depot stock healthy' },
            { name: 'Prayagraj District', facilities: 24, beds: '71% Occ', status: 'Low', alert: 'All vitals green' },
            { name: 'Meerut District', facilities: 20, beds: '76% Occ', status: 'Moderate', alert: 'Ambulance response 9m' },
          ].map((dist) => (
            <div
              key={dist.name}
              className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-xs text-slate-100">{dist.name}</div>
                  <div className="text-[11px] text-slate-400">{dist.facilities} Connected Units</div>
                </div>
                <Badge level={dist.status.toLowerCase() as any}>{dist.status}</Badge>
              </div>
              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800 text-slate-400">
                <span>Beds: {dist.beds}</span>
                <span className="text-amber-400 truncate max-w-[120px]">{dist.alert}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default StateDashboardPage;
