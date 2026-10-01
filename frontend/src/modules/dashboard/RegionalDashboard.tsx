import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import { Link } from 'react-router-dom';
import {
  MapPin,
  Building,
  Bed,
  Package,
  AlertTriangle,
  Download,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export const RegionalDashboard: React.FC = () => {
  const [selectedState, setSelectedState] = useState('Uttar Pradesh');
  const [selectedDistrict, setSelectedDistrict] = useState('Lucknow');
  const toast = useToast();

  const handleExportReport = () => {
    toast.success('Report Export Initiated', `Generated official PDF bulletin for ${selectedDistrict}, ${selectedState}.`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header and Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
            <MapPin className="w-3.5 h-3.5" />
            <span>Regional Administrative Grid</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            State & District Resource Intelligence Command
          </h2>
          <p className="text-xs text-slate-400">
            Micro-level health resource monitoring, facility drilldowns, and inter-district benchmarking.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none"
          >
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="Bihar">Bihar</option>
            <option value="Delhi">Delhi</option>
            <option value="Rajasthan">Rajasthan</option>
            <option value="Madhya Pradesh">Madhya Pradesh</option>
          </select>

          <select
            value={selectedDistrict}
            onChange={(e) => setSelectedDistrict(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none"
          >
            <option value="Lucknow">Lucknow District</option>
            <option value="Kanpur">Kanpur District</option>
            <option value="Varanasi">Varanasi District</option>
            <option value="Patna">Patna District</option>
            <option value="New Delhi">New Delhi Central</option>
          </select>

          <button
            onClick={handleExportReport}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 text-xs font-semibold transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export District Bulletin</span>
          </button>
        </div>
      </div>

      {/* District KPI Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>Primary & Secondary Centers</span>
            <Building className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">42 Centers</div>
          <span className="text-[11px] text-slate-500 mt-2 block">1 DH, 8 CHCs, 33 PHCs</span>
        </Card>

        <Card>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>District Bed Occupancy</span>
            <Bed className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">87.4% Full</div>
          <span className="text-[11px] text-amber-400 mt-2 block">126 ICU beds vacant</span>
        </Card>

        <Card>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>Essential Medicine Stock</span>
            <Package className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">74.2% Adequate</div>
          <span className="text-[11px] text-rose-400 mt-2 block">2 facilities in critical deficit</span>
        </Card>

        <Card>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>District Resilience Score</span>
            <TrendingUp className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">81.5 / 100</div>
          <span className="text-[11px] text-emerald-400 mt-2 block">Tier-2 Resilient</span>
        </Card>
      </div>

      {/* Comparative View Link */}
      <Card className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 to-slate-900/60 border-slate-800">
        <div>
          <h3 className="font-bold text-sm text-slate-100">Inter-District Resource Comparison (Feature 69)</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Benchmark {selectedDistrict} alongside neighboring healthcare jurisdictions to identify mutual redistribution paths.
          </p>
        </div>
        <Link
          to="/map"
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-md shadow-emerald-500/10 transition-all shrink-0"
        >
          <span>Open Full Comparison Map</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </Card>
    </div>
  );
};

export default RegionalDashboard;
