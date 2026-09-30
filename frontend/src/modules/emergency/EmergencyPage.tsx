import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle } from 'react-leaflet';
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
  MapPin,
  HeartPulse,
  Activity,
  Wind,
  Layers,
  Sparkles,
} from 'lucide-react';

interface DistrictPriority {
  district: string;
  state: string;
  vulnerabilityIndex: number;
  deficit: string;
  recommendation: string;
  lat: number;
  lng: number;
}

const districtPriorities: DistrictPriority[] = [
  { district: 'Patna', state: 'Bihar', vulnerabilityIndex: 94, deficit: 'Oxygen (-58%), ICU (-82%)', recommendation: 'Dispatch 120 O2 cylinders from Kanpur depot', lat: 25.5941, lng: 85.1376 },
  { district: 'Lucknow', state: 'Uttar Pradesh', vulnerabilityIndex: 88, deficit: 'Paracetamol IV (-45%), Ventilators (-68%)', recommendation: 'Redirect 400 bottles from Varanasi', lat: 26.8467, lng: 80.9462 },
  { district: 'Gorakhpur', state: 'Uttar Pradesh', vulnerabilityIndex: 82, deficit: 'Pediatric Staff (-50%)', recommendation: 'Deploy 8 mobile doctor reserve units', lat: 26.7606, lng: 83.3732 },
  { district: 'Muzaffarpur', state: 'Bihar', vulnerabilityIndex: 79, deficit: 'Antibiotics (-38%)', recommendation: 'Release national buffer stock tranche #3', lat: 26.1209, lng: 85.3647 },
];

export const EmergencyPage: React.FC = () => {
  const [isCrisisActive, setIsCrisisActive] = useState(true);
  const [surgeMultiplier, setSurgeMultiplier] = useState(35);
  const [selectedDisasterType, setSelectedDisasterType] = useState('Epidemic Outbreak');
  const [selectedEpicenter, setSelectedEpicenter] = useState('Patna, Bihar');
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [hasSimulated, setHasSimulated] = useState(true);

  const toast = useToast();

  const handleRunSimulation = () => {
    setSimulationRunning(true);
    setTimeout(() => {
      setSimulationRunning(false);
      setHasSimulated(true);
      toast.success(
        'What-If Simulation Completed',
        `Simulated ${surgeMultiplier}% surge in ${selectedDisasterType} around ${selectedEpicenter}. Generated optimal resource rerouting paths.`,
        5000
      );
    }, 1100);
  };

  const handleMobilizeFleet = (district: string) => {
    toast.success(
      'Emergency Logistics Escort Dispatched',
      `Mobilized green-corridor convoy with 80 O2 cylinders to ${district}. GPS tracker: CONVOY-99.`,
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
                {isCrisisActive && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                  </span>
                )}
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

      {/* Resource Shortage Panel (Required by Phase 8) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2 border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Critical Oxygen Deficit</span>
            <Wind className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400">-580 Cylinders</div>
          <div className="text-[11px] text-slate-400">Buffer runway: 11.2 hours remaining</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>ICU Bed Saturation</span>
            <HeartPulse className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">96.8% Occupied</div>
          <div className="text-[11px] text-slate-400">Surge triage protocol triggered</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2 border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Essential Antivirals / IV</span>
            <Activity className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-rose-400">-4,200 Units</div>
          <div className="text-[11px] text-slate-400">Rebalance tranche authorized</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Rapid Response Fleets</span>
            <Truck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">12 Convoys</div>
          <div className="text-[11px] text-emerald-400">Green corridor police escort ready</div>
        </Card>
      </div>

      {/* Crisis Map & District Priority Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Crisis Map (Required by Phase 8) */}
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-bold text-slate-100">Live Crisis Map & Containment Zones</h3>
            </div>
            <span className="text-xs font-mono text-rose-400">4 Red Zones</span>
          </div>

          <div className="h-72 w-full rounded-xl overflow-hidden border border-slate-800">
            <MapContainer center={[26.0, 83.0]} zoom={6} scrollWheelZoom={false} className="h-full w-full">
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />
              {districtPriorities.map((dp) => (
                <React.Fragment key={dp.district}>
                  <Circle
                    center={[dp.lat, dp.lng]}
                    radius={35000}
                    pathOptions={{
                      fillColor: '#ef4444',
                      fillOpacity: 0.35,
                      color: '#dc2626',
                      weight: 2,
                    }}
                  />
                  <CircleMarker
                    center={[dp.lat, dp.lng]}
                    radius={10}
                    pathOptions={{
                      fillColor: '#ef4444',
                      fillOpacity: 0.9,
                      color: '#ffffff',
                      weight: 2,
                    }}
                  >
                    <Popup>
                      <div className="p-1 text-xs space-y-1">
                        <strong className="text-white font-bold">{dp.district} ({dp.state})</strong>
                        <div className="text-rose-300 font-mono">Vulnerability: {dp.vulnerabilityIndex}/100</div>
                        <div className="text-slate-300 text-[11px]">{dp.deficit}</div>
                      </div>
                    </Popup>
                  </CircleMarker>
                </React.Fragment>
              ))}
            </MapContainer>
          </div>
        </Card>

        {/* District Priority Table (Required by Phase 8) */}
        <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-2">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100">Vulnerability Deficit Priority Matrix & Roster</h3>
            <span className="text-[11px] text-slate-400 font-mono">Ranked by Deficit Index</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">District</th>
                  <th className="py-2.5 px-3">Vulnerability</th>
                  <th className="py-2.5 px-3">Critical Deficit</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {districtPriorities.map((dp) => (
                  <tr key={dp.district} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3">
                      <div className="font-bold text-slate-100">{dp.district}</div>
                      <div className="text-[10px] text-slate-400">{dp.state}</div>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold text-rose-400">
                      {dp.vulnerabilityIndex} / 100
                    </td>
                    <td className="py-2.5 px-3 text-[11px] text-slate-300">
                      <div>{dp.deficit}</div>
                      <div className="text-emerald-400 text-[10px]">{dp.recommendation}</div>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleMobilizeFleet(dp.district)}
                        className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-semibold transition-colors"
                      >
                        Mobilize
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Scenario Simulation Form & What-If Comparison (Required by Phase 8) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scenario Form */}
        <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100">Scenario Simulation Engine</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Disaster Scenario Type</label>
              <select
                value={selectedDisasterType}
                onChange={(e) => setSelectedDisasterType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
              >
                <option value="Epidemic Outbreak">Epidemic Outbreak (Dengue/Chikungunya)</option>
                <option value="Respiratory Pandemic Surge">Respiratory Surge (Influenza/COVID)</option>
                <option value="Industrial Toxic Release">Industrial Chemical Leak / Blast</option>
                <option value="Flood Monsoon Disaster">Monsoon Water-Borne Disaster</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Epicenter District</label>
              <select
                value={selectedEpicenter}
                onChange={(e) => setSelectedEpicenter(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
              >
                <option value="Patna, Bihar">Patna, Bihar</option>
                <option value="Gorakhpur, Uttar Pradesh">Gorakhpur, Uttar Pradesh</option>
                <option value="Lucknow, Uttar Pradesh">Lucknow, Uttar Pradesh</option>
                <option value="Muzaffarpur, Bihar">Muzaffarpur, Bihar</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-300 font-medium">Surge Magnitude (+%)</span>
                <span className="font-mono text-rose-400 font-bold">+{surgeMultiplier}% Influx</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={surgeMultiplier}
                onChange={(e) => setSurgeMultiplier(Number(e.target.value))}
                className="w-full accent-rose-500 cursor-pointer"
              />
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={simulationRunning}
              className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {simulationRunning ? (
                <span>Solving Constraint Matrices...</span>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Compute Resilience Impact</span>
                </>
              )}
            </button>
          </div>
        </Card>

        {/* What-If Comparison Cards (Required by Phase 8) */}
        <Card className="lg:col-span-2 p-5 bg-slate-900 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              What-If Comparative Impact Assessment
            </h3>
            <span className="text-xs font-mono text-emerald-400">Baseline vs +{surgeMultiplier}% Crisis</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {/* Metric 1 */}
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-medium">ICU Bed Saturation</span>
              <div className="flex items-baseline justify-between pt-1">
                <span className="text-slate-400">Baseline: <strong>81%</strong></span>
                <span className="text-rose-400 font-mono font-bold text-base">Surge: {Math.min(100, 81 + Math.round(surgeMultiplier * 0.4))}%</span>
              </div>
              <div className="text-[11px] text-amber-400">
                Delta: +{Math.round(surgeMultiplier * 0.4)}% deficit without rerouting
              </div>
            </div>

            {/* Metric 2 */}
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-medium">Oxygen Stockout Runway</span>
              <div className="flex items-baseline justify-between pt-1">
                <span className="text-slate-400">Baseline: <strong>18 hrs</strong></span>
                <span className="text-rose-400 font-mono font-bold text-base">Surge: {Math.max(2, Math.round(18 - surgeMultiplier * 0.15))} hrs</span>
              </div>
              <div className="text-[11px] text-rose-400">
                Lead time deficit: Immediate green corridor mandatory
              </div>
            </div>

            {/* Metric 3 */}
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <span className="text-slate-400 font-medium">Potential Avoidable Fatalities</span>
              <div className="flex items-baseline justify-between pt-1">
                <span className="text-slate-400">Unmanaged: <strong>48</strong></span>
                <span className="text-emerald-400 font-mono font-bold text-base">With Solver: 2</span>
              </div>
              <div className="text-[11px] text-emerald-400">
                95.8% Risk mitigated with inter-district rebalancing
              </div>
            </div>
          </div>

          {/* AI Automated Recommendations (Required by Phase 8) */}
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs space-y-1.5">
            <span className="font-bold text-emerald-300 block">AI Emergency Recommendations:</span>
            <ul className="list-disc pl-4 space-y-1 text-slate-300 text-[11px]">
              <li>Reallocate 120 Oxygen D-type cylinders from Kanpur Central Store Depot to {selectedEpicenter}.</li>
              <li>Activate mutual-aid standby pact with 3 private tertiary medical colleges within 40km.</li>
              <li>Deploy 4 advanced mobile surgical triage vans from Lucknow reserve.</li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default EmergencyPage;
