import React, { useState } from 'react';
import { MOCK_FACILITIES, FacilityMapItem } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Building2,
  Search,
  MapPin,
  Bed,
  Package,
  Activity,
  PhoneCall,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const FacilitiesPage: React.FC = () => {
  const [facilities] = useState<FacilityMapItem[]>(MOCK_FACILITIES);
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('All');

  const types = ['All', 'PHC', 'CHC', 'District Hospital', 'Medical College', 'Warehouse'];

  const filtered = facilities.filter((f) => {
    if (selectedType !== 'All' && f.type !== selectedType) return false;
    if (
      search &&
      !f.name.toLowerCase().includes(search.toLowerCase()) &&
      !f.district.toLowerCase().includes(search.toLowerCase()) &&
      !f.state.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
            <Building2 className="w-3.5 h-3.5" />
            <span>Healthcare Infrastructure Directory</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Facilities, Hospitals & Medical Depots
          </h2>
          <p className="text-xs text-slate-400">
            Directory of connected primary health centers, tertiary care hospitals, and regional warehouses.
          </p>
        </div>

        <Link
          to="/map"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
        >
          <MapPin className="w-4 h-4 text-cyan-400" />
          <span>Switch to Geospatial Map</span>
        </Link>
      </div>

      {/* Filter and Search */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-[260px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search facility name, district, or state..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
            >
              {types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        <span className="text-xs text-slate-400">
          Total: <strong className="text-slate-100">{filtered.length}</strong> facilities
        </span>
      </Card>

      {/* Facilities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.map((f) => (
          <Card key={f.id} className="flex flex-col justify-between space-y-4 hover:border-slate-600 transition-colors">
            <div>
              <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-slate-800/80 text-blue-400 border border-slate-700/60 mt-0.5">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-100">{f.name}</h3>
                    <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <MapPin className="w-3 h-3 text-cyan-400" />
                      <span>{f.district}, {f.state}</span>
                      <span>•</span>
                      <span className="text-teal-400 font-mono text-[11px]">{f.type}</span>
                    </div>
                  </div>
                </div>
                <Badge level={f.risk_level}>{f.risk_level.toUpperCase()}</Badge>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs pt-3 font-mono">
                <div className="p-2 bg-slate-950/70 rounded-xl">
                  <span className="text-[10px] text-slate-500 block">Medicine Stock</span>
                  <strong className="text-emerald-400">{f.medicine_availability_pct}%</strong>
                </div>
                <div className="p-2 bg-slate-950/70 rounded-xl">
                  <span className="text-[10px] text-slate-500 block">Bed Occupancy</span>
                  <strong className="text-cyan-400">{f.bed_occupancy_pct}%</strong>
                </div>
                <div className="p-2 bg-slate-950/70 rounded-xl">
                  <span className="text-[10px] text-slate-500 block">Free ICU Beds</span>
                  <strong className="text-purple-400">{f.icu_beds_free}</strong>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                <span>Staff: <strong className="text-slate-200">{f.staff_status}</strong></span>
                <span>O2 Buffer: <strong className="text-amber-400 font-mono">{f.oxygen_supply_hours} hrs</strong></span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-[11px] font-mono text-slate-500">ID: {f.id}</span>
              <Link
                to="/inventory"
                className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 text-[11px]"
              >
                <span>View Stock Ledger</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default FacilitiesPage;
