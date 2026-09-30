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
  Users,
  Map,
  AlertTriangle,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Download,
  Filter,
  RefreshCw,
  Truck,
  HeartPulse,
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

export const DistrictDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const districtName = user?.district || 'Lucknow';
  const stateName = user?.state || 'Uttar Pradesh';
  const [selectedType, setSelectedType] = useState<string>('All');
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const toast = useToast();

  const types = ['All', 'Hospital', 'CHC', 'PHC'];

  const facilityUtilizationData = [
    { facility: 'District Hospital', beds: 92, ambulances: 4, stockCover: 14 },
    { facility: 'CHC Malihabad', beds: 78, ambulances: 2, stockCover: 18 },
    { facility: 'CHC Bakshi Talab', beds: 84, ambulances: 2, stockCover: 16 },
    { facility: 'PHC Mohanlalganj', beds: 65, ambulances: 1, stockCover: 22 },
    { facility: 'PHC Chinhat', beds: 71, ambulances: 1, stockCover: 20 },
  ];

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date().toLocaleTimeString());
      toast.success('District Telemetry Updated', `Live feed refreshed for ${districtName} health network.`);
    }, 600);
  };

  const handleExport = () => {
    toast.success('District Report Exported', `Generated ${districtName} CMO official situation briefing.`);
  };

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

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Updated: <strong className="text-slate-200 font-mono">{lastUpdated}</strong></span>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
            title="Refresh District Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export District Bulletin</span>
          </button>

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

      {/* Filter Bar */}
      <Card className="p-3.5 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">Filter Unit Tier:</span>
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
        <div className="text-xs text-slate-400">
          Jurisdiction: <strong className="text-slate-100">{districtName} CMO Zone</strong>
        </div>
      </Card>

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
            <span>District Bed Census</span>
            <Bed className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">86.2%</div>
          <div className="text-[11px] text-purple-400">48 Free ICU & Ventilators</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Ambulance Readiness</span>
            <Truck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">18 / 20</div>
          <div className="text-[11px] text-emerald-400">Average response time: 8.4 mins</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Critical Drugs Runway</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">14.2 Days</div>
          <div className="text-[11px] text-rose-400">Insulin restock needed at 2 PHCs</div>
        </Card>
      </div>

      {/* District Alert Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-rose-300">PHC Malihabad Insulin Low Stock</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Available vials will deplete in 2.8 days at current dispensing rate. Local depot rebalancing suggested.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-start gap-3">
          <Truck className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-cyan-300">ALS Ambulance Convoy Fleet Active</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              3 Advanced Life Support ambulances prepositioned along Highway Corridor 24 for trauma readiness.
            </p>
          </div>
        </div>
      </div>

      {/* Facility Utilization Chart */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100">District Center Resource Utilization</h3>
            <p className="text-[11px] text-slate-400">Bed Occupancy % vs Days of Medicine Cover per Facility</p>
          </div>
          <span className="text-xs font-mono text-cyan-400">{districtName} Health Sector</span>
        </div>

        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={facilityUtilizationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="facility" stroke="#64748b" tick={{ fontSize: 10 }} />
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
              <Bar dataKey="beds" fill="#06b6d4" name="Bed Occupancy %" radius={[4, 4, 0, 0]} />
              <Bar dataKey="stockCover" fill="#10b981" name="Stock Cover (Days)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Facility Census Overview */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-100">District Healthcare Centers Roster</h3>
          <span className="text-xs text-slate-400">Showing 5 primary hubs</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { name: 'Dr. RML District Hospital', type: 'District Hospital', beds: '92% (14 Free)', stock: '14d cover', status: 'high' as const },
            { name: 'Malihabad Community Health Center', type: 'CHC', beds: '78% (8 Free)', stock: '3d cover (LOW)', status: 'critical' as const },
            { name: 'Bakshi Ka Talab CHC', type: 'CHC', beds: '84% (6 Free)', stock: '18d cover', status: 'moderate' as const },
            { name: 'Mohanlalganj PHC', type: 'PHC', beds: '65% (12 Free)', stock: '22d cover', status: 'low' as const },
          ].map((fac) => (
            <div key={fac.name} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-bold text-xs text-slate-100">{fac.name}</div>
                  <span className="text-[10px] text-teal-400 font-mono">{fac.type}</span>
                </div>
                <Badge level={fac.status}>{fac.status.toUpperCase()}</Badge>
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                <span>Beds: {fac.beds}</span>
                <span className="font-mono text-slate-200">{fac.stock}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default DistrictDashboardPage;
