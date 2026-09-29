import React from 'react';
import { MOCK_WORKFORCE } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Users, UserCheck, Stethoscope, AlertTriangle, ShieldCheck } from 'lucide-react';

export const WorkforcePage: React.FC = () => {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-pink-500/10 text-pink-400 border border-pink-500/30">
          <Users className="w-3.5 h-3.5" />
          <span>Clinical & Paramedical Roster</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
          Workforce Telemetry & Doctor-to-Patient Ratios
        </h2>
        <p className="text-xs text-slate-400">
          Shift attendance logging, departmental fatigue levels, and dynamic rota balancing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {MOCK_WORKFORCE.map((w) => (
          <Card key={w.department} className="space-y-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-sm text-slate-100">{w.department}</h3>
                <span className="text-xs text-slate-400">Active Shift Telemetry</span>
              </div>
              <Badge level={w.stress_index}>{w.stress_index.toUpperCase()} LOAD</Badge>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="p-2.5 bg-slate-950/70 rounded-xl">
                <span className="text-[10px] text-slate-500 block">Doctors On Duty</span>
                <strong className="text-emerald-400 text-sm">{w.doctors_on_duty}</strong>
              </div>
              <div className="p-2.5 bg-slate-950/70 rounded-xl">
                <span className="text-[10px] text-slate-500 block">Nurses & Paramedics</span>
                <strong className="text-teal-400 text-sm">{w.nurses_on_duty}</strong>
              </div>
              <div className="p-2.5 bg-slate-950/70 rounded-xl">
                <span className="text-[10px] text-slate-500 block">Doctor : Patient</span>
                <strong className="text-purple-400 text-sm">{w.doctor_patient_ratio}</strong>
              </div>
            </div>

            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>Shift Attendance:</span>
                <strong className="text-slate-200 font-mono">{w.shift_attendance_pct}%</strong>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${w.shift_attendance_pct}%` }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default WorkforcePage;
