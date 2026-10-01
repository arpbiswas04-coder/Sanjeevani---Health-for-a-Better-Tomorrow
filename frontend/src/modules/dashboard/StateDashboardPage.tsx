import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/store/authStore';
import { useToast } from '@/hooks/useToast';
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
  Download,
  Filter,
  RefreshCw,
  Clock,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { MOCK_FACILITIES } from '@/services/mockData';

export const StateDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const assignedState = user?.state || 'Uttar Pradesh';
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const toast = useToast();

  const stateFacilities = MOCK_FACILITIES.filter(
    (f) => f.state.toLowerCase() === assignedState.toLowerCase()
  );

  const districts = ['All', 'Lucknow', 'Varanasi', 'Gorakhpur', 'Kanpur Nagar', 'Prayagraj', 'Meerut'];
  const types = ['All', 'PHC', 'CHC', 'District Hospital', 'Medical College', 'Warehouse'];

  const districtChartData = [
    { district: 'Lucknow', bedOccupancy: 88, medicineCover: 16 },
    { district: 'Varanasi', bedOccupancy: 74, medicineCover: 22 },
    { district: 'Gorakhpur', bedOccupancy: 82, medicineCover: 12 },
    { district: 'Kanpur', bedOccupancy: 79, medicineCover: 24 },
    { district: 'Prayagraj', bedOccupancy: 71, medicineCover: 19 },
    { district: 'Meerut', bedOccupancy: 76, medicineCover: 18 },
  ];

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date().toLocaleTimeString());
      toast.success('State Telemetry Synced', `Updated telemetry for ${assignedState} health network.`);
    }, 600);
  };

  const handleExport = () => {
    toast.success('State Bulletin Exported', `Generated ${assignedState} Health Authority situation report.`);
  };

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

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Updated: <strong className="text-slate-200 font-mono">{lastUpdated}</strong></span>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            title="Refresh State Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export State Bulletin</span>
          </button>

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

      {/* Drilldown Filter Controls */}
      <Card className="p-3.5 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">District:</span>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
            >
              {districts.map((d) => (
                <option key={d} value={d}>{d}</option>
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
        </div>

        <div className="text-xs text-slate-400">
          State Scope: <strong className="text-slate-100">{assignedState}</strong>
        </div>
      </Card>

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

      {/* State Alert Cards Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-amber-300">Gorakhpur Pediatric Staff Deficit</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Doctor-to-patient ratio reached 1:42 due to seasonal viral encephalitis admissions. Mobile medical teams alerted.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-emerald-300">Central Medical Depot Buffer Optimal</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              CMSD Lucknow confirmed receipt of 50,000 antibiotic vials and 400 cylinders of liquid oxygen.
            </p>
          </div>
        </div>
      </div>

      {/* District Benchmarking Chart */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100">District Healthcare Load Comparison</h3>
            <p className="text-[11px] text-slate-400">Bed Occupancy % vs Days of Medicine Cover per District</p>
          </div>
          <span className="text-xs font-mono text-emerald-400">{assignedState}</span>
        </div>

        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={districtChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="district" stroke="#64748b" tick={{ fontSize: 11 }} />
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
              <Bar dataKey="bedOccupancy" fill="#a855f7" name="Bed Occupancy %" radius={[4, 4, 0, 0]} />
              <Bar dataKey="medicineCover" fill="#10b981" name="Medicine Cover (Days)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

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
