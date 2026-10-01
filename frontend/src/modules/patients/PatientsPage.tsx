import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { UserCheck, Clock, Users, Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export const PatientsPage: React.FC = () => {
  const footfallData = [
    { hour: '08:00', opd: 210, emergency: 42, ipd: 15 },
    { hour: '10:00', opd: 480, emergency: 68, ipd: 32 },
    { hour: '12:00', opd: 620, emergency: 85, ipd: 48 },
    { hour: '14:00', opd: 390, emergency: 62, ipd: 28 },
    { hour: '16:00', opd: 450, emergency: 74, ipd: 38 },
    { hour: '18:00', opd: 310, emergency: 92, ipd: 45 },
    { hour: '20:00', opd: 140, emergency: 88, ipd: 22 },
  ];

  const triageQueues = [
    { tier: 'Red (Immediate Life-Saving)', waitTime: '0 mins', activePatients: 6, doctorRatio: '1:1', status: 'critical' as const },
    { tier: 'Orange (Very Urgent)', waitTime: '8 mins', activePatients: 24, doctorRatio: '1:4', status: 'high' as const },
    { tier: 'Yellow (Urgent)', waitTime: '22 mins', activePatients: 78, doctorRatio: '1:12', status: 'moderate' as const },
    { tier: 'Green (Standard OPD)', waitTime: '38 mins', activePatients: 194, doctorRatio: '1:32', status: 'low' as const },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
          <UserCheck className="w-3.5 h-3.5" />
          <span>Patient Admissions & Flow Telemetry</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
          Patient Footfall, Queue Times & Triage Saturation
        </h2>
        <p className="text-xs text-slate-400">
          Real-time patient influx telemetry across emergency departments, general OPDs, and in-patient wards.
        </p>
      </div>

      {/* Hourly Influx Graph */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Hourly Patient Influx Curve</h3>
            <p className="text-[11px] text-slate-400">OPD vs Emergency Department registrations</p>
          </div>
          <span className="text-xs font-mono text-emerald-400">Peak: 12:00 PM</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={footfallData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#f8fafc',
                }}
              />
              <Area type="monotone" dataKey="opd" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="OPD Footfall" />
              <Area type="monotone" dataKey="emergency" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.2} name="Emergency" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Triage Queues List */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {triageQueues.map((q) => (
          <Card key={q.tier} className="space-y-3">
            <div className="flex items-center justify-between">
              <Badge level={q.status}>{q.status.toUpperCase()}</Badge>
              <span className="text-[10px] font-mono text-slate-400">{q.doctorRatio}</span>
            </div>
            <h4 className="font-bold text-xs text-slate-200">{q.tier}</h4>
            <div className="flex justify-between items-baseline pt-1">
              <div>
                <span className="text-2xl font-bold font-mono text-slate-100">{q.activePatients}</span>
                <span className="text-[11px] text-slate-400 ml-1">in queue</span>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-cyan-400 font-bold">{q.waitTime}</span>
                <span className="text-[10px] text-slate-500 block">avg wait</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default PatientsPage;
