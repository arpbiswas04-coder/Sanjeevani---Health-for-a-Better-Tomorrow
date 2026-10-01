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
  Wrench,
  Truck,
  Clock,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Download,
  Filter,
  RefreshCw,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

export const FacilityDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const facilityName = user?.facilityName || 'Dr. RML Hospital, Lucknow';
  const districtName = user?.district || 'Lucknow';
  const [selectedWard, setSelectedWard] = useState<string>('All');
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const toast = useToast();

  const wards = ['All', 'Emergency ICU', 'Cardiac Care Unit (CCU)', 'Pediatric Ward', 'General Medicine', 'Surgical Ward'];

  const hourlyFlowData = [
    { hour: '06:00', admissions: 12, discharges: 4 },
    { hour: '09:00', admissions: 34, discharges: 18 },
    { hour: '12:00', admissions: 52, discharges: 31 },
    { hour: '15:00', admissions: 38, discharges: 24 },
    { hour: '18:00', admissions: 29, discharges: 15 },
    { hour: '21:00', admissions: 19, discharges: 8 },
  ];

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date().toLocaleTimeString());
      toast.success('Hospital Telemetry Refreshed', `Census synchronized for ${facilityName}.`);
    }, 600);
  };

  const handleExport = () => {
    toast.success('Facility Report Exported', `Generated operational shift handover briefing for ${facilityName}.`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Facility Operational Authority</span>
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight mt-1 flex items-center gap-2">
            {facilityName}
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700">
              FACILITY_ADMIN
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Local bed census, pharmacy stock ledger, biomedical equipment health, and clinical staffing roster in {districtName}.
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
            title="Refresh Census"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-purple-400' : ''}`} />
          </button>

          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Handover</span>
          </button>

          <Link
            to="/facility/stock"
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-colors shadow-sm shadow-emerald-500/20"
          >
            <Package className="w-4 h-4" />
            Pharmacy Stock
          </Link>
          <Link
            to="/facility/beds"
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-bold transition-colors"
          >
            <Bed className="w-4 h-4 text-purple-400" />
            Bed Allocation
          </Link>
        </div>
      </div>

      {/* Ward Filter Bar */}
      <Card className="p-3.5 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">Select Ward / Department:</span>
          <select
            value={selectedWard}
            onChange={(e) => setSelectedWard(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
          >
            {wards.map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
        <div className="text-xs text-slate-400">
          Showing: <strong className="text-slate-100">{selectedWard === 'All' ? 'All Inpatient Wards' : selectedWard}</strong>
        </div>
      </Card>

      {/* Facility Operations KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Bed Occupancy</span>
            <Bed className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400">92.0%</div>
          <div className="text-[11px] text-slate-400">4 ICU & 12 General Vacant</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Essential Medicines</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-amber-400">91% Ready</div>
          <div className="text-[11px] text-slate-400">2 Items at Reorder Threshold</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Medical Equipment Health</span>
            <Wrench className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400">98.2% Up</div>
          <div className="text-[11px] text-slate-400">1 Defibrillator in Maintenance</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Shift Staffing Roster</span>
            <Users className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">42 On Duty</div>
          <div className="text-[11px] text-slate-400">Doctor-Patient 1:18 (Manageable)</div>
        </Card>
      </div>

      {/* Facility Alert Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-amber-300">Oxygen Buffer At 9 Hours Capacity</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Cylinder manifold buffer is at 9 hours of emergency reserves. Refill truck ETA: 2.5 hours.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-emerald-300">Biomedical Equipment Calibrated</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              All 14 ICU ventilators and neonatal incubators passed automated self-diagnostics.
            </p>
          </div>
        </div>
      </div>

      {/* Hourly Admission vs Discharge Curve */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100">Today's Patient Census Flow Dynamics</h3>
            <p className="text-[11px] text-slate-400">Hourly Admissions vs Discharges across all active wards</p>
          </div>
          <span className="text-xs font-mono text-purple-400">Live Telemetry</span>
        </div>

        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={hourlyFlowData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 11 }} />
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
              <Area type="monotone" dataKey="admissions" stroke="#a855f7" fill="#a855f7" fillOpacity={0.2} name="Admissions" />
              <Area type="monotone" dataKey="discharges" stroke="#10b981" fill="#10b981" fillOpacity={0.2} name="Discharges" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};

export default FacilityDashboardPage;
