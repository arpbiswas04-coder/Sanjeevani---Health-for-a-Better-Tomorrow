import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  AlertTriangle,
  Flame,
  Radio,
  Send,
  Sliders,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Truck,
  CheckCircle2,
} from 'lucide-react';

export const EmergencyPage: React.FC = () => {
  const [isCrisisActive, setIsCrisisActive] = useState(true);
  const [surgeMultiplier, setSurgeMultiplier] = useState(30);
  const [selectedDisasterType, setSelectedDisasterType] = useState('Epidemic Outbreak');
  const [simulationRunning, setSimulationRunning] = useState(false);
  const toast = useToast();

  const districtPriorities = [
    { district: 'Patna', state: 'Bihar', vulnerabilityIndex: 94, deficit: 'Oxygen (-58%), ICU (-82%)', recommendation: 'Dispatch 120 O2 cylinders from Kanpur depot' },
    { district: 'Lucknow', state: 'Uttar Pradesh', vulnerabilityIndex: 88, deficit: 'Paracetamol IV (-45%), Ventilators (-68%)', recommendation: 'Redirect 400 bottles from Varanasi' },
    { district: 'Gorakhpur', state: 'Uttar Pradesh', vulnerabilityIndex: 82, deficit: 'Pediatric Staff (-50%)', recommendation: 'Deploy 8 mobile doctor reserve units' },
    { district: 'Muzaffarpur', state: 'Bihar', vulnerabilityIndex: 79, deficit: 'Antibiotics (-38%)', recommendation: 'Release national buffer stock tranche #3' },
  ];

  const handleRunSimulation = () => {
    setSimulationRunning(true);
    setTimeout(() => {
      setSimulationRunning(false);
      toast.success(
        'Simulation Completed',
        `Simulated ${surgeMultiplier}% surge in ${selectedDisasterType}. OR-Tools optimization generated 4 emergency transfer paths.`,
        5000
      );
    }, 1200);
  };

  const handleMobilizeFleet = (district: string) => {
    toast.success(
      'Emergency Convoys Mobilized',
      `Authorized priority logistics convoy for ${district} with GPS real-time escort.`,
      4000
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Crisis Banner */}
      <div className="relative overflow-hidden rounded-2xl p-6 border border-rose-500/30 bg-gradient-to-r from-rose-950/60 via-slate-900 to-slate-900 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-3 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-400 shrink-0">
              <Flame className="w-6 h-6 animate-bounce" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
                  DEFCON-1 Active
                </span>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                </span>
              </div>
              <h2 className="text-2xl font-black text-white mt-1">
                Emergency Command & Crisis Mobilization
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Centralized disaster override mode. Linear programming solvers actively computing inter-district relief redistribution.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsCrisisActive(!isCrisisActive);
                toast.info('Status Changed', `Emergency Mode: ${!isCrisisActive ? 'Engaged' : 'Standby'}`);
              }}
              className={`px-4 py-2 rounded-xl text-xs font-bold border transition-colors ${
                isCrisisActive
                  ? 'bg-rose-500 hover:bg-rose-600 text-white border-rose-400 shadow-lg shadow-rose-500/20'
                  : 'bg-slate-800 text-slate-300 border-slate-700'
              }`}
            >
              {isCrisisActive ? 'DISENGAGE CRISIS' : 'ACTIVATE CRISIS MODE'}
            </button>
          </div>
        </div>
      </div>

      {/* District Priority Table & What-If Simulation Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* District Priority Table */}
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Vulnerability Deficit Priority Matrix
              </h3>
              <p className="text-[11px] text-slate-400">
                Ranked by AI deficit risk score combining stockouts, ICU saturation, and epidemic trajectory.
              </p>
            </div>
            <Badge level="critical">Priority 1 Ranked</Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">District</th>
                  <th className="py-2.5 px-3">Index</th>
                  <th className="py-2.5 px-3">Identified Deficit</th>
                  <th className="py-2.5 px-3">Algorithmic Recommendation</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {districtPriorities.map((row) => (
                  <tr key={row.district} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-100">{row.district}</div>
                      <div className="text-[10px] text-slate-500">{row.state}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono font-bold text-rose-400">
                        {row.vulnerabilityIndex}/100
                      </span>
                    </td>
                    <td className="py-3 px-3 text-rose-300 text-[11px] font-mono">
                      {row.deficit}
                    </td>
                    <td className="py-3 px-3 text-slate-300 text-[11px]">
                      {row.recommendation}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleMobilizeFleet(row.district)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[11px] font-semibold rounded-lg transition-colors"
                      >
                        <Truck className="w-3 h-3" />
                        <span>Mobilize</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* What-If Scenario Simulator */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              Scenario Simulation Engine
            </h3>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed">
            Test grid resilience under hypothetical emergency surges using Monte Carlo and Google OR-Tools solvers.
          </p>

          <div className="space-y-3 pt-1">
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                Disaster / Incident Archetype
              </label>
              <select
                value={selectedDisasterType}
                onChange={(e) => setSelectedDisasterType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none"
              >
                <option value="Epidemic Outbreak">Epidemic Outbreak (Vector / Airborne)</option>
                <option value="Mass Casualty Incident">Mass Casualty Incident (Industrial/Transit)</option>
                <option value="Flooding & Extreme Weather">Flooding & Supply Chain Isolation</option>
                <option value="Cold-Chain Disruption">Cold-Chain Power Grid Outage</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Demand Surge Stress:</span>
                <strong className="font-mono text-cyan-400">+{surgeMultiplier}%</strong>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={surgeMultiplier}
                onChange={(e) => setSurgeMultiplier(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Predicted Stockout Horizon:</span>
                <strong className="text-rose-400 font-mono">2.4 days</strong>
              </div>
              <div className="flex justify-between">
                <span>Required Buffer Influx:</span>
                <strong className="text-amber-400 font-mono">48,200 units</strong>
              </div>
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={simulationRunning}
              className="w-full py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2"
            >
              {simulationRunning ? (
                <span>Solving Constraint Matrices...</span>
              ) : (
                <>
                  <TrendingUp className="w-4 h-4" />
                  <span>Compute Resilience Impact</span>
                </>
              )}
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default EmergencyPage;
