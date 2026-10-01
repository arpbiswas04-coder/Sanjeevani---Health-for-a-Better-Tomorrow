import React, { useState } from 'react';
import { MOCK_BEDS, MOCK_FACILITIES } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Bed,
  Activity,
  HeartPulse,
  Wind,
  CheckCircle2,
  AlertTriangle,
  Send,
  Building2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export const BedsPage: React.FC = () => {
  const [beds] = useState(MOCK_BEDS);
  const toast = useToast();

  const chartData = MOCK_FACILITIES.map((f) => ({
    name: f.name.split(' ')[0],
    occupancy: f.bed_occupancy_pct,
    freeIcu: f.icu_beds_free,
  }));

  const handleReserveBed = (facilityName: string) => {
    toast.success(
      'Emergency Bed Allocated',
      `Reserved 1 Critical ICU bed at ${facilityName}. Ambulance telemetry notified.`,
      4000
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            <Bed className="w-3.5 h-3.5" />
            <span>Ward & ICU Telemetry</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Real-Time Bed Availability & Ventilator Occupancy
          </h2>
          <p className="text-xs text-slate-400">
            Continuous telemetry feed from hospital admissions, triage desks, and discharge systems.
          </p>
        </div>

        <div className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs font-mono">
          Total Monitored Beds: <strong className="text-emerald-400">11,820</strong>
        </div>
      </div>

      {/* Bed Category Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {beds.map((b) => (
          <Card key={b.type} className="flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-purple-400">
                  {b.type.includes('ICU') && <HeartPulse className="w-5 h-5 text-rose-400" />}
                  {b.type.includes('Ventilator') && <Wind className="w-5 h-5 text-cyan-400" />}
                  {b.type.includes('Oxygen') && <Activity className="w-5 h-5 text-amber-400" />}
                  {b.type.includes('General') && <Bed className="w-5 h-5 text-emerald-400" />}
                </div>
                <Badge level={b.status}>{b.occupancy_rate}% Occupied</Badge>
              </div>

              <h3 className="text-xs font-medium text-slate-400">{b.type}</h3>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-2xl font-bold font-mono text-slate-100">
                  {b.available}
                </span>
                <span className="text-xs text-slate-400">vacant of {b.total}</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Occupied: {b.occupied}</span>
                <span>Free: {b.available}</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    b.occupancy_rate > 90
                      ? 'bg-rose-500'
                      : b.occupancy_rate > 80
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{ width: `${b.occupancy_rate}%` }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Hospital Occupancy Chart & Allocation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">
                Facility Bed Occupancy Rates (%)
              </h3>
              <p className="text-[11px] text-slate-400">
                Saturation levels across regional healthcare centers
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Live Telemetry</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Bar dataKey="occupancy" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Occupancy %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Rapid ICU Reservation Feed */}
        <Card className="flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <HeartPulse className="w-4 h-4 text-rose-400" />
              Rapid Emergency Bed Triage
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              Select verified vacant ICU bed for urgent patient routing:
            </p>
          </div>

          <div className="space-y-2.5 overflow-y-auto max-h-64">
            {MOCK_FACILITIES.filter((f) => f.icu_beds_free > 0).map((f) => (
              <div
                key={f.id}
                className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="font-semibold text-xs text-slate-100">{f.name}</div>
                  <div className="text-[10px] text-slate-400">{f.district} • {f.icu_beds_free} free ICU beds</div>
                </div>
                <button
                  onClick={() => handleReserveBed(f.name)}
                  className="px-2.5 py-1 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-semibold rounded-lg transition-colors"
                >
                  Allocate
                </button>
              </div>
            ))}
          </div>

          <div className="p-2.5 bg-slate-950/60 border border-slate-800/80 rounded-xl text-[10px] text-slate-400">
            Emergency lock holds bed for 45 minutes while ambulance en route.
          </div>
        </Card>
      </div>
    </div>
  );
};

export default BedsPage;
