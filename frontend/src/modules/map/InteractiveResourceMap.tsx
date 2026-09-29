import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { MOCK_FACILITIES, FacilityMapItem } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { RiskLevel } from '@/types';
import {
  MapPin,
  Search,
  Filter,
  Building2,
  Bed,
  Package,
  Users,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';

export const InteractiveResourceMap: React.FC = () => {
  const [selectedState, setSelectedState] = useState<string>('All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedRisk, setSelectedRisk] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const states = useMemo(() => {
    return ['All', ...new Set(MOCK_FACILITIES.map((f) => f.state))];
  }, []);

  const types = ['All', 'PHC', 'CHC', 'District Hospital', 'Medical College', 'Warehouse'];
  const risks = ['All', 'low', 'moderate', 'high', 'critical'];

  const filteredFacilities = useMemo(() => {
    return MOCK_FACILITIES.filter((f) => {
      if (selectedState !== 'All' && f.state !== selectedState) return false;
      if (selectedType !== 'All' && f.type !== selectedType) return false;
      if (selectedRisk !== 'All' && f.risk_level !== selectedRisk) return false;
      if (
        searchQuery &&
        !f.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !f.district.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [selectedState, selectedType, selectedRisk, searchQuery]);

  const riskColors: Record<RiskLevel, { fill: string; stroke: string }> = {
    low: { fill: '#10b981', stroke: '#059669' },
    moderate: { fill: '#f59e0b', stroke: '#d97706' },
    high: { fill: '#f97316', stroke: '#ea580c' },
    critical: { fill: '#f43f5e', stroke: '#e11d48' },
  };

  return (
    <div className="space-y-5 animate-in fade-in duration-300">
      {/* Top Header & Metrics Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <MapPin className="w-3.5 h-3.5" />
            <span>Interactive Health Resource & Supply Chain Map</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Geospatial Healthcare Network Telemetry
          </h2>
          <p className="text-xs text-slate-400">
            Live monitoring of {MOCK_FACILITIES.length} regional healthcare nodes, depots, and triage facilities.
          </p>
        </div>

        {/* Quick Summary Chips */}
        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Nodes Visible:</span>{' '}
            <strong className="text-emerald-400 font-mono">{filteredFacilities.length}</strong>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">High/Critical Risk:</span>{' '}
            <strong className="text-rose-400 font-mono">
              {filteredFacilities.filter((f) => f.risk_level === 'high' || f.risk_level === 'critical').length}
            </strong>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search facility name, city, district..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          {/* State Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">State:</span>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
            >
              {states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Facility Type Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Type:</span>
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

          {/* Risk Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Risk:</span>
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none uppercase"
            >
              {risks.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          <button
            onClick={() => {
              setSelectedState('All');
              setSelectedType('All');
              setSelectedRisk('All');
              setSearchQuery('');
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
            title="Reset Filters"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate-400 border-t border-slate-800/60">
          <span className="font-semibold text-slate-300">Resilience Risk Legend:</span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Low Risk (Optimal)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> Moderate
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block" /> High Shortage
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block animate-pulse" /> Critical Outbreak / Crisis
          </span>
        </div>
      </Card>

      {/* Map Viewport Container */}
      <div className="h-[600px] w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative">
        <MapContainer
          center={[26.5, 80.5]}
          zoom={6}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          {/* CartoDB Dark Matter Tiles */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {filteredFacilities.map((facility: FacilityMapItem) => {
            const colors = riskColors[facility.risk_level];

            return (
              <CircleMarker
                key={facility.id}
                center={[facility.latitude, facility.longitude]}
                radius={facility.risk_level === 'critical' ? 14 : facility.risk_level === 'high' ? 11 : 9}
                pathOptions={{
                  fillColor: colors.fill,
                  fillOpacity: 0.85,
                  color: colors.stroke,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="p-1 space-y-2 min-w-[240px]">
                    <div className="flex items-start justify-between gap-2 border-b border-slate-700/60 pb-1.5">
                      <div>
                        <h4 className="font-bold text-xs text-white leading-tight">
                          {facility.name}
                        </h4>
                        <span className="text-[10px] text-slate-400">
                          {facility.district}, {facility.state}
                        </span>
                      </div>
                      <Badge level={facility.risk_level}>{facility.risk_level.toUpperCase()}</Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div className="p-1.5 bg-slate-800/80 rounded-lg">
                        <span className="text-[10px] text-slate-400 block">Medicine Stock</span>
                        <strong className="text-emerald-400 font-mono">
                          {facility.medicine_availability_pct}% Available
                        </strong>
                      </div>
                      <div className="p-1.5 bg-slate-800/80 rounded-lg">
                        <span className="text-[10px] text-slate-400 block">Bed Occupancy</span>
                        <strong className="text-cyan-400 font-mono">
                          {facility.bed_occupancy_pct}% Full
                        </strong>
                      </div>
                      <div className="p-1.5 bg-slate-800/80 rounded-lg">
                        <span className="text-[10px] text-slate-400 block">Free ICU Beds</span>
                        <strong className="text-purple-400 font-mono">
                          {facility.icu_beds_free} beds
                        </strong>
                      </div>
                      <div className="p-1.5 bg-slate-800/80 rounded-lg">
                        <span className="text-[10px] text-slate-400 block">O2 Supply Buffer</span>
                        <strong className="text-amber-400 font-mono">
                          {facility.oxygen_supply_hours} hrs
                        </strong>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 pt-1 flex items-center justify-between border-t border-slate-700/60">
                      <span>Staff Status: <strong className="text-slate-200">{facility.staff_status}</strong></span>
                      <span className="text-teal-400 font-mono">{facility.type}</span>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};

export default InteractiveResourceMap;
