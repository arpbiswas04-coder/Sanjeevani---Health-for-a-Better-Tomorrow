import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Activity,
  Wrench,
  CheckCircle2,
  AlertOctagon,
  Cpu,
  Truck,
  Radio,
  MapPin,
  Clock,
  BatteryCharging,
  Send,
} from 'lucide-react';

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

interface AmbulanceItem {
  id: string;
  callsign: string;
  type: 'Advanced Life Support (ALS)' | 'Basic Life Support (BLS)' | 'Neonatal Transport (NICU)';
  baseFacility: string;
  currentSector: string;
  status: 'Available (Standby)' | 'Dispatched (En Route)' | 'At Patient Scene' | 'Under Sanitization';
  etaMinutes: number;
  oxygenLevelPct: number;
  crew: string;
}

export const EquipmentPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'equipment' | 'ambulances'>('equipment');

  const [equipmentList] = useState<EquipmentItem[]>([
    { id: 'eq-001', name: 'ICU Turbine Ventilator (Servo-Air)', facility: 'Patna Sadar Hospital', status: 'Operational', uptime_pct: 99.4, last_service: '2026-08-14', next_service_due: '2026-11-14', serial_number: 'SN-VENT-9921' },
    { id: 'eq-002', name: 'Medical Oxygen PSA Plant (500 LPM)', facility: 'RML Lucknow Hospital', status: 'Maintenance Required', uptime_pct: 92.1, last_service: '2026-06-10', next_service_due: '2026-10-05', serial_number: 'PSA-OXY-4421' },
    { id: 'eq-003', name: 'Hemodialysis Unit (Fresenius 4008S)', facility: 'AIIMS New Delhi', status: 'Operational', uptime_pct: 98.9, last_service: '2026-09-01', next_service_due: '2026-12-01', serial_number: 'DIA-FRES-1044' },
    { id: 'eq-004', name: 'Biphasic Defibrillator Monitor', facility: 'PHC Malihabad', status: 'Critical Failure', uptime_pct: 64.0, last_service: '2026-03-22', next_service_due: 'Overdue (38 days)', serial_number: 'DEF-ZOL-7781' },
    { id: 'eq-005', name: 'Automated External Defibrillator (AED)', facility: 'Varanasi Rural CHC', status: 'Operational', uptime_pct: 100.0, last_service: '2026-07-19', next_service_due: '2026-10-19', serial_number: 'AED-PHI-3319' },
  ]);

  const [ambulanceList, setAmbulanceList] = useState<AmbulanceItem[]>([
    {
      id: 'amb-101',
      callsign: 'Sanjeevani Fleet ALS-01',
      type: 'Advanced Life Support (ALS)',
      baseFacility: 'AIIMS New Delhi Trauma Center',
      currentSector: 'Ring Road South Sector 4',
      status: 'Available (Standby)',
      etaMinutes: 6,
      oxygenLevelPct: 98,
      crew: 'Dr. Neha Sen + 2 EMTs',
    },
    {
      id: 'amb-102',
      callsign: 'Rapid Response BLS-09',
      type: 'Basic Life Support (BLS)',
      baseFacility: 'Patna Sadar Hospital',
      currentSector: 'Gandhi Maidan Sector',
      status: 'Dispatched (En Route)',
      etaMinutes: 11,
      oxygenLevelPct: 89,
      crew: 'EMT Ramesh Kumar + 1 Paramedic',
    },
    {
      id: 'amb-103',
      callsign: 'Neonatal Care NICU-02',
      type: 'Neonatal Transport (NICU)',
      baseFacility: 'RML Hospital Lucknow',
      currentSector: 'Gomti Nagar Expressway',
      status: 'At Patient Scene',
      etaMinutes: 4,
      oxygenLevelPct: 95,
      crew: 'Pediatric Specialist + Incubator Tech',
    },
    {
      id: 'amb-104',
      callsign: 'Critical Transfer ALS-04',
      type: 'Advanced Life Support (ALS)',
      baseFacility: 'Varanasi Rural CHC',
      currentSector: 'Depot Sanitization Bay',
      status: 'Under Sanitization',
      etaMinutes: 25,
      oxygenLevelPct: 100,
      crew: 'EMT S. Tiwari',
    },
  ]);

  const toast = useToast();

  const handleDispatchEngineer = (item: EquipmentItem) => {
    toast.success('Biomedical Engineer Dispatched', `Service ticket generated for ${item.name} at ${item.facility}. High priority routing.`);
  };

  const handleDispatchAmbulance = (amb: AmbulanceItem) => {
    setAmbulanceList((prev) =>
      prev.map((a) =>
        a.id === amb.id ? { ...a, status: 'Dispatched (En Route)', etaMinutes: 8 } : a
      )
    );
    toast.success(
      'Emergency Dispatch Sent',
      `${amb.callsign} (${amb.type}) dispatched with GPS escort. Target ETA: 8 minutes.`
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Cpu className="w-3.5 h-3.5" />
            <span>Health Resource Infrastructure • Phase 6</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Biomedical Equipment & Ambulance Fleet Telemetry
          </h2>
          <p className="text-xs text-slate-400">
            Preventative apparatus calibration, PSA oxygen plant pressure monitors, and real-time GPS ambulance dispatch.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('equipment')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'equipment'
                ? 'bg-cyan-500 text-slate-950 shadow-sm shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-4 h-4" />
            Biomedical Equipment ({equipmentList.length})
          </button>
          <button
            onClick={() => setActiveTab('ambulances')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'ambulances'
                ? 'bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Truck className="w-4 h-4" />
            Ambulance Fleet ({ambulanceList.length})
          </button>
        </div>
      </div>

      {activeTab === 'equipment' ? (
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
      ) : (
        /* Ambulance Status Tab */
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400">Total Fleet Active</span>
              <div className="text-2xl font-black text-slate-100 font-mono mt-1">{ambulanceList.length}</div>
              <span className="text-[10px] text-emerald-400">GPS Monitored</span>
            </div>
            <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-500/30">
              <span className="text-[10px] uppercase font-bold text-emerald-400">Available Standby</span>
              <div className="text-2xl font-black text-emerald-300 font-mono mt-1">
                {ambulanceList.filter((a) => a.status.includes('Available')).length}
              </div>
              <span className="text-[10px] text-slate-400">Ready for instant dispatch</span>
            </div>
            <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30">
              <span className="text-[10px] uppercase font-bold text-amber-400">En Route / On Scene</span>
              <div className="text-2xl font-black text-amber-300 font-mono mt-1">
                {ambulanceList.filter((a) => a.status.includes('Dispatched') || a.status.includes('Scene')).length}
              </div>
              <span className="text-[10px] text-slate-400">Average ETA: 7 mins</span>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-cyan-400">Oxygen Preparedness</span>
              <div className="text-2xl font-black text-cyan-300 font-mono mt-1">95.5%</div>
              <span className="text-[10px] text-slate-400">Cylinder Pressure Normal</span>
            </div>
          </div>

          <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Ambulance Callsign</th>
                    <th className="py-3 px-4">Type / Capability</th>
                    <th className="py-3 px-4">Base Facility</th>
                    <th className="py-3 px-4">Current GPS Sector</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">O2 Level</th>
                    <th className="py-3 px-4">Crew Assigned</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {ambulanceList.map((amb) => (
                    <tr key={amb.id} className="hover:bg-slate-800/40">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-100 flex items-center gap-1.5">
                          <Truck className="w-3.5 h-3.5 text-emerald-400" />
                          {amb.callsign}
                        </div>
                        <div className="text-[10px] font-mono text-slate-500">{amb.id}</div>
                      </td>
                      <td className="py-3.5 px-4 font-medium text-slate-300">{amb.type}</td>
                      <td className="py-3.5 px-4 text-slate-300">{amb.baseFacility}</td>
                      <td className="py-3.5 px-4 font-mono text-slate-400 flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-cyan-400 shrink-0" />
                        {amb.currentSector}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${
                            amb.status.includes('Available')
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : amb.status.includes('Dispatched')
                              ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                              : amb.status.includes('Scene')
                              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {amb.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                        {amb.oxygenLevelPct}%
                      </td>
                      <td className="py-3.5 px-4 text-[11px] text-slate-400">{amb.crew}</td>
                      <td className="py-3.5 px-4 text-right">
                        {amb.status.includes('Available') ? (
                          <button
                            onClick={() => handleDispatchAmbulance(amb)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-lg transition-colors shadow-sm shadow-emerald-500/20"
                          >
                            <Send className="w-3 h-3" />
                            Dispatch
                          </button>
                        ) : (
                          <span className="text-[11px] font-mono text-slate-500">ETA {amb.etaMinutes}m</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default EquipmentPage;
