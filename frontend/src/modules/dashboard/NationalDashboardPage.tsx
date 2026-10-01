import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  Package,
  Bed,
  TrendingUp,
  AlertTriangle,
  Download,
  Filter,
  RefreshCw,
  Clock,
  Map,
  Activity,
  Flame,
  Truck,
  HeartPulse,
  Send,
  Sparkles,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { MOCK_FACILITIES } from '@/services/mockData';

export const NationalDashboardPage: React.FC = () => {
  const [selectedState, setSelectedState] = useState<string>('All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedRisk, setSelectedRisk] = useState<string>('All');
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const toast = useToast();

  const states = ['All', 'Uttar Pradesh', 'Bihar', 'Delhi', 'Rajasthan', 'Madhya Pradesh'];
  const types = ['All', 'PHC', 'CHC', 'District Hospital', 'Medical College', 'Warehouse'];
  const risks = ['All', 'low', 'moderate', 'high', 'critical'];

  const filteredFacilities = MOCK_FACILITIES.filter((f) => {
    if (selectedState !== 'All' && f.state !== selectedState) return false;
    if (selectedType !== 'All' && f.type !== selectedType) return false;
    if (selectedRisk !== 'All' && f.risk_level !== selectedRisk) return false;
    return true;
  });

  const stateComparisonData = [
    { state: 'Uttar Pradesh', bedOccupancy: 81, medicineDays: 18, riskScore: 28 },
    { state: 'Bihar', bedOccupancy: 89, medicineDays: 9, riskScore: 62 },
    { state: 'Delhi', bedOccupancy: 76, medicineDays: 24, riskScore: 18 },
    { state: 'Rajasthan', bedOccupancy: 72, medicineDays: 21, riskScore: 22 },
    { state: 'Madhya Pradesh', bedOccupancy: 84, medicineDays: 14, riskScore: 45 },
  ];

  const footfallTrendData = [
    { day: 'Mon', opd: 38400, emergency: 6200 },
    { day: 'Tue', opd: 42100, emergency: 6800 },
    { day: 'Wed', opd: 46500, emergency: 7400 },
    { day: 'Thu', opd: 44200, emergency: 7100 },
    { day: 'Fri', opd: 48900, emergency: 8200 },
    { day: 'Sat', opd: 39500, emergency: 8900 },
    { day: 'Sun', opd: 28200, emergency: 9400 },
  ];

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date().toLocaleTimeString());
      toast.success('Telemetry Synchronized', 'Retrieved latest hospital telemetry from 1,428 mesh nodes.');
    }, 700);
  };

  const handleExport = (format: 'PDF' | 'CSV' | 'JSON') => {
    toast.success(
      'National Health Bulletin Generated',
      `Exported national health grid situation report in ${format} format.`,
      4000
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top National Command Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>National Health Command HQ • MoHFW Apex Mesh</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-100 tracking-tight mt-1 flex items-center gap-2.5">
            National Health Resource Command
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              NATIONAL_ADMIN
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time geospatial health telemetry across 36 states/UTs, 766 districts, and 1,428 connected tertiary & primary care nodes.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Updated: <strong className="text-slate-200 font-mono">{lastUpdated}</strong></span>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          {/* Export Dropdown Group */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => handleExport('PDF')}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-all shadow-md shadow-emerald-500/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export PDF Bulletin</span>
            </button>
            <button
              onClick={() => handleExport('CSV')}
              className="px-2.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
              title="Export CSV dataset"
            >
              CSV
            </button>
          </div>
        </div>
      </div>

      {/* Drill-down Filters Bar */}
      <Card className="p-4 bg-slate-900/90 border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 font-medium">State:</span>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
              >
                {states.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400 font-medium">Facility Tier:</span>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
              >
                {types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400 font-medium">Risk Status:</span>
              <select
                value={selectedRisk}
                onChange={(e) => setSelectedRisk(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none uppercase"
              >
                {risks.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Drilldown: <strong className="text-emerald-400 font-mono">{filteredFacilities.length}</strong> matching facilities
          </div>
        </div>
      </Card>

      {/* National KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>National Bed Occupancy</span>
            <Bed className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">82.4%</div>
          <div className="text-[11px] text-purple-400 flex items-center justify-between">
            <span>1,120 Critical ICU Vacant</span>
            <span className="text-slate-500">Normal Range</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>National Medicine Runway</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">21.8 Days</div>
          <div className="text-[11px] text-rose-400 flex items-center justify-between">
            <span>14 Low Stock Alerts Active</span>
            <span className="text-slate-500">Lead: 6.2d</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Grid Resilience Index</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400">94.8 / 100</div>
          <div className="text-[11px] text-emerald-400 flex items-center justify-between">
            <span>+2.4 pts vs previous 30d</span>
            <span className="text-slate-500">High Stability</span>
          </div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Emergencies</span>
            <Flame className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400">3 Hotspots</div>
          <div className="text-[11px] text-rose-300 flex items-center justify-between">
            <span>Dengue (UP), Encephalitis (BR)</span>
            <span className="text-slate-500">Defcon-2</span>
          </div>
        </Card>
      </div>

      {/* Critical National Alerts Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              CRITICAL STOCK DEFICIT
            </span>
            <span className="text-[10px] font-mono text-rose-300">Bihar MSD</span>
          </div>
          <h4 className="font-semibold text-xs text-slate-100">
            Patna District Insulin & IV Fluids runway under 48 hours
          </h4>
          <p className="text-[11px] text-slate-400">
            Centralized replenishment tranche of 8,000 vials queued for dispatch from Lucknow CMSD.
          </p>
          <div className="pt-1 flex justify-end">
            <Link
              to="/national/inventory"
              className="text-[11px] text-rose-400 hover:text-rose-300 font-semibold underline"
            >
              Review Transfer Authorization →
            </Link>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" />
              EPIDEMIOLOGICAL SURGE
            </span>
            <span className="text-[10px] font-mono text-amber-300">Eastern UP</span>
          </div>
          <h4 className="font-semibold text-xs text-slate-100">
            Dengue positive cluster spike in Gorakhpur and Varanasi (+38%)
          </h4>
          <p className="text-[11px] text-slate-400">
            Platelet kits and NS1 antigen diagnostic supplies mobilized across 18 Community Health Centers.
          </p>
          <div className="pt-1 flex justify-end">
            <Link
              to="/national/disease"
              className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold underline"
            >
              Open Outbreak Heatmap →
            </Link>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              FEDERATED AI ROUND SYNC
            </span>
            <span className="text-[10px] font-mono text-cyan-300">Round #42</span>
          </div>
          <h4 className="font-semibold text-xs text-slate-100">
            Global demand prediction accuracy achieved 96.8%
          </h4>
          <p className="text-[11px] text-slate-400">
            Edge nodes across AIIMS, RML, and Patna completed gradient aggregation without clinical data egress.
          </p>
          <div className="pt-1 flex justify-end">
            <Link
              to="/national/federated-ai"
              className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold underline"
            >
              Inspect Node Convergence →
            </Link>
          </div>
        </div>
      </div>

      {/* National Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* State Resilience Benchmark Bar Chart */}
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">State Resilience & Resource Benchmarks</h3>
              <p className="text-[11px] text-slate-400">Bed Occupancy % vs Days of Medicine Cover</p>
            </div>
            <span className="text-xs font-mono text-emerald-400">5 Regional Zones</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateComparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="state" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="bedOccupancy" fill="#8b5cf6" name="Bed Occupancy %" radius={[4, 4, 0, 0]} />
                <Bar dataKey="medicineDays" fill="#10b981" name="Medicine Cover (Days)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 7-Day National Influx Curve Area Chart */}
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">7-Day National Influx Curve</h3>
              <p className="text-[11px] text-slate-400">Daily OPD Admissions vs Emergency Triage Registrations</p>
            </div>
            <span className="text-xs font-mono text-cyan-400">Peak: Friday Surge</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={footfallTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Area type="monotone" dataKey="opd" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.2} name="OPD Admissions" />
                <Area type="monotone" dataKey="emergency" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.2} name="Emergency Triage" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Quick Launchpad to Modules */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link
          to="/national/map"
          className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-800/80 transition-all flex items-center gap-3 group"
        >
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:scale-110 transition-transform">
            <Map className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-xs text-slate-200">Interactive Map</div>
            <div className="text-[10px] text-slate-400">Geospatial Telemetry</div>
          </div>
        </Link>

        <Link
          to="/national/inventory"
          className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/50 hover:bg-slate-800/80 transition-all flex items-center gap-3 group"
        >
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 group-hover:scale-110 transition-transform">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-xs text-slate-200">Stock & Batches</div>
            <div className="text-[10px] text-slate-400">Redistribution Ledger</div>
          </div>
        </Link>

        <Link
          to="/national/emergency"
          className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-rose-500/50 hover:bg-slate-800/80 transition-all flex items-center gap-3 group"
        >
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 group-hover:scale-110 transition-transform">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-xs text-slate-200">Emergency Mode</div>
            <div className="text-[10px] text-slate-400">What-If Simulation</div>
          </div>
        </Link>

        <Link
          to="/national/federated-ai"
          className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-teal-500/50 hover:bg-slate-800/80 transition-all flex items-center gap-3 group"
        >
          <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400 group-hover:scale-110 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-xs text-slate-200">Federated AI</div>
            <div className="text-[10px] text-slate-400">Edge Privacy Mesh</div>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default NationalDashboardPage;
