import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/store/authStore';
import { Link } from 'react-router-dom';
import {
  Building2,
  Package,
  Bed,
  Users,
  Map,
  AlertTriangle,
  Clock,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';

export const DistrictDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const districtName = user?.district || 'Lucknow';
  const stateName = user?.state || 'Uttar Pradesh';

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>District Health Authority Jurisdiction</span>
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight mt-1 flex items-center gap-2">
            {districtName} District Command Desk
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
              DISTRICT_ADMIN
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Local jurisdiction triage, emergency ambulance fleet routing, and Primary Health Center oversight in {stateName}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/district/map"
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-colors shadow-sm shadow-emerald-500/20"
          >
            <Map className="w-4 h-4" />
            District Resource Map
          </Link>
          <Link
            to="/district/alerts"
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-bold transition-colors"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            District Alerts
          </Link>
        </div>
      </div>

      {/* District Telemetry KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>District Facilities</span>
            <Building2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">28 Units</div>
          <div className="text-[11px] text-slate-400">4 Hospitals, 12 CHCs, 12 PHCs</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>ICU Saturation</span>
            <Bed className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400">89.4%</div>
          <div className="text-[11px] text-rose-300">Surge diversion protocol armed</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Triage Wait Time</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">18.5 min</div>
          <div className="text-[11px] text-emerald-400">-4 mins from yesterday</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>District Staff on Duty</span>
            <Users className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">412 Staff</div>
          <div className="text-[11px] text-slate-400">92.4% Shift Attendance</div>
        </Card>
      </div>

      {/* Facilities in District */}
      <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-cyan-400" />
            Healthcare Centers Monitored within {districtName}
          </h3>
          <span className="text-xs text-slate-400">Restricted to District Jurisdiction</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { name: 'Dr. Ram Manohar Lohia Hospital', type: 'District Hospital', beds: '92% (14 Free)', stock: 'High Risk (Insulin Deficit)', staff: '128 on duty' },
            { name: 'King George Medical Center Satellite', type: 'Specialized Center', beds: '84% (28 Free)', stock: 'Normal', staff: '84 on duty' },
            { name: 'Malihabad Primary Health Center', type: 'PHC', beds: '65% (12 Free)', stock: 'Critical (Paracetamol Infusion)', staff: '14 on duty' },
            { name: 'Bakshi Ka Talab Community Health Center', type: 'CHC', beds: '72% (18 Free)', stock: 'Normal', staff: '26 on duty' },
          ].map((fac) => (
            <div
              key={fac.name}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-xs text-slate-100">{fac.name}</div>
                  <div className="text-[10px] text-slate-400">{fac.type}</div>
                </div>
                <Badge level={fac.stock.includes('Critical') ? 'critical' : fac.stock.includes('High') ? 'high' : 'low'}>
                  {fac.beds}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800 text-slate-400">
                <span>Stock: <strong className="text-slate-200">{fac.stock}</strong></span>
                <span>{fac.staff}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default DistrictDashboardPage;
