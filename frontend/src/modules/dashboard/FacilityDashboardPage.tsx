import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/store/authStore';
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
} from 'lucide-react';

export const FacilityDashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const facilityName = user?.facilityName || 'Dr. RML Hospital, Lucknow';
  const districtName = user?.district || 'Lucknow';

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

        <div className="flex items-center gap-2">
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
            <span>On-Hand Drug Inventory</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">4,820 Units</div>
          <div className="text-[11px] text-rose-300">1 Critical Batch Expiring</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Staff Attendance Today</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">92.4%</div>
          <div className="text-[11px] text-emerald-400">18 Doctors, 42 Nurses Active</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Biomedical Uptime</span>
            <Wrench className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">96.8%</div>
          <div className="text-[11px] text-slate-400">PSA Oxygen Plant Online</div>
        </Card>
      </div>

      {/* Facility Quick Operations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-5 bg-slate-900 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Package className="w-4 h-4 text-amber-400" />
              Critical Stock Expiry & Shortages
            </h3>
            <Link to="/facility/expiry" className="text-xs text-emerald-400 hover:underline">
              View All FEFO Batches →
            </Link>
          </div>
          <div className="space-y-2 text-xs">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
              <div>
                <div className="font-bold text-slate-100">Insulin Human Regular (100 IU/mL)</div>
                <div className="text-[10px] text-slate-400">Batch: INS-8841-A • 120 vials on hand</div>
              </div>
              <Badge level="critical">19 Days Left</Badge>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
              <div>
                <div className="font-bold text-slate-100">Medical Oxygen (Type-D 47L)</div>
                <div className="text-[10px] text-slate-400">Pressure: 4.8 bar • 45 Cylinders</div>
              </div>
              <Badge level="high">4.8 Days Supply</Badge>
            </div>
          </div>
        </Card>

        <Card className="p-5 bg-slate-900 border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Truck className="w-4 h-4 text-emerald-400" />
              Assigned Ambulance Fleet
            </h3>
            <Link to="/facility/ambulance" className="text-xs text-emerald-400 hover:underline">
              Manage Fleet →
            </Link>
          </div>
          <div className="space-y-2 text-xs">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
              <div>
                <div className="font-bold text-slate-100">Sanjeevani Fleet ALS-01</div>
                <div className="text-[10px] text-slate-400">Advanced Life Support • O2 98%</div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Standby Ready
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex justify-between items-center">
              <div>
                <div className="font-bold text-slate-100">Rapid Response BLS-09</div>
                <div className="text-[10px] text-slate-400">Basic Life Support • En Route</div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                ETA 11 min
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default FacilityDashboardPage;
