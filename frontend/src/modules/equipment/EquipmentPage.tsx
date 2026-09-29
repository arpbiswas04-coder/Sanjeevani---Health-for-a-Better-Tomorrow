import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import { Activity, Wrench, CheckCircle2, AlertOctagon, Cpu, Power, ShieldAlert } from 'lucide-react';

interface EquipmentItem {
  id: string;
  name: string;
  facility: string;
  status: 'Operational' | 'Maintenance Required' | 'Critical Failure';
  uptime_pct: number;
  last_service: string;
  next_service_due: string;
  serial_number: string;
}

export const EquipmentPage: React.FC = () => {
  const [equipmentList] = useState<EquipmentItem[]>([
    { id: 'eq-001', name: 'ICU Turbine Ventilator (Servo-Air)', facility: 'Patna Sadar Hospital', status: 'Operational', uptime_pct: 99.4, last_service: '2026-08-14', next_service_due: '2026-11-14', serial_number: 'SN-VENT-9921' },
    { id: 'eq-002', name: 'Medical Oxygen PSA Plant (500 LPM)', facility: 'RML Lucknow Hospital', status: 'Maintenance Required', uptime_pct: 92.1, last_service: '2026-06-10', next_service_due: '2026-10-05', serial_number: 'PSA-OXY-4421' },
    { id: 'eq-003', name: 'Hemodialysis Unit (Fresenius 4008S)', facility: 'AIIMS New Delhi', status: 'Operational', uptime_pct: 98.9, last_service: '2026-09-01', next_service_due: '2026-12-01', serial_number: 'DIA-FRES-1044' },
    { id: 'eq-004', name: 'Biphasic Defibrillator Monitor', facility: 'PHC Malihabad', status: 'Critical Failure', uptime_pct: 64.0, last_service: '2026-03-22', next_service_due: 'Overdue (38 days)', serial_number: 'DEF-ZOL-7781' },
    { id: 'eq-005', name: 'Automated External Defibrillator (AED)', facility: 'Varanasi Rural CHC', status: 'Operational', uptime_pct: 100.0, last_service: '2026-07-19', next_service_due: '2026-10-19', serial_number: 'AED-PHI-3319' },
  ]);
  const toast = useToast();

  const handleDispatchEngineer = (item: EquipmentItem) => {
    toast.success('Biomedical Engineer Dispatched', `Service ticket generated for ${item.name} at ${item.facility}. High priority routing.`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Cpu className="w-3.5 h-3.5" />
            <span>Biomedical Asset Management</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Biomedical Equipment & Oxygen Plants Telemetry
          </h2>
          <p className="text-xs text-slate-400">
            Preventative maintenance tracking, sensor telemetry, and fault diagnosis for critical clinical apparatus.
          </p>
        </div>

        <div className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs">
          Operational Rate: <strong className="text-emerald-400 font-mono">92.4% Online</strong>
        </div>
      </div>

      <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Equipment / Apparatus</th>
                <th className="py-3 px-4">Facility</th>
                <th className="py-3 px-4">Uptime %</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Next Calibration Due</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {equipmentList.map((eq) => (
                <tr key={eq.id} className="hover:bg-slate-800/40">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-100">{eq.name}</div>
                    <div className="text-[10px] font-mono text-slate-500">{eq.serial_number}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{eq.facility}</td>
                  <td className="py-3 px-4 font-mono font-bold text-slate-100">{eq.uptime_pct}%</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded-full ${
                        eq.status === 'Operational'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : eq.status === 'Maintenance Required'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {eq.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300">{eq.next_service_due}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDispatchEngineer(eq)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-semibold rounded-lg transition-colors"
                    >
                      <Wrench className="w-3 h-3 text-cyan-400" />
                      <span>Service</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default EquipmentPage;
