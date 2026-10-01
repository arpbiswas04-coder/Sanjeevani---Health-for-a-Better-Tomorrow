import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Popup } from 'react-leaflet';
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
  Boxes,
  Flame,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';

interface HeatmapHotspot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  radiusMeters: number;
  disease: string;
  severity: 'high' | 'critical';
  caseCount: number;
}

const mockDiseaseHotspots: HeatmapHotspot[] = [
  { id: 'dh-01', name: 'Gorakhpur Encephalitis Zone', lat: 26.76, lng: 83.37, radiusMeters: 35000, disease: 'Japanese Encephalitis', severity: 'critical', caseCount: 420 },
  { id: 'dh-02', name: 'Lucknow Dengue Hotspot', lat: 26.8467, lng: 80.9462, radiusMeters: 28000, disease: 'Dengue Serotype 2', severity: 'high', caseCount: 310 },
  { id: 'dh-03', name: 'Patna Water-Borne Cluster', lat: 25.5941, lng: 85.1376, radiusMeters: 30000, disease: 'Acute Diarrheal Outbreak', severity: 'critical', caseCount: 540 },
  { id: 'dh-04', name: 'Varanasi Malaria Vector Zone', lat: 25.3176, lng: 82.9739, radiusMeters: 22000, disease: 'Falciparum Malaria', severity: 'high', caseCount: 195 },
];

const mockEmergencyHotspots = [
  { id: 'em-01', name: 'Patna Sadar Critical Oxygen Crisis', lat: 25.61, lng: 85.15, radiusMeters: 25000, alert: 'Oxygen Runway < 12 hrs', severity: 'critical' },
  { id: 'em-02', name: 'Gorakhpur Pediatric ICU Deficit', lat: 26.78, lng: 83.39, radiusMeters: 20000, alert: 'ICU Saturation 98%', severity: 'critical' },
];

export const InteractiveResourceMap: React.FC = () => {
  const [selectedState, setSelectedState] = useState<string>('All');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedRisk, setSelectedRisk] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Layer Toggles
  const [showFacilities, setShowFacilities] = useState<boolean>(true);
  const [showWarehouses, setShowWarehouses] = useState<boolean>(true);
  const [showDiseaseHeatmap, setShowDiseaseHeatmap] = useState<boolean>(false);
  const [showEmergencyHeatmap, setShowEmergencyHeatmap] = useState<boolean>(false);

  const states = useMemo(() => {
    return ['All', ...new Set(MOCK_FACILITIES.map((f) => f.state))];
  }, []);

  const districts = useMemo(() => {
    const pool = selectedState === 'All'
      ? MOCK_FACILITIES
      : MOCK_FACILITIES.filter((f) => f.state === selectedState);
    return ['All', ...new Set(pool.map((f) => f.district))];
  }, [selectedState]);

  const types = ['All', 'PHC', 'CHC', 'District Hospital', 'Medical College', 'Warehouse'];
  const risks = ['All', 'low', 'moderate', 'high', 'critical'];

  const filteredFacilities = useMemo(() => {
    return MOCK_FACILITIES.filter((f) => {
      if (selectedState !== 'All' && f.state !== selectedState) return false;
      if (selectedDistrict !== 'All' && f.district !== selectedDistrict) return false;
      if (selectedType !== 'All' && f.type !== selectedType) return false;
      if (selectedRisk !== 'All' && f.risk_level !== selectedRisk) return false;
      if (f.type === 'Warehouse' && !showWarehouses) return false;
      if (f.type !== 'Warehouse' && !showFacilities) return false;
      if (
        searchQuery &&
        !f.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !f.district.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [selectedState, selectedDistrict, selectedType, selectedRisk, searchQuery, showFacilities, showWarehouses]);

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
            Live monitoring of primary health centers, tertiary care hospitals, central warehouses, and epidemiological risk heatmaps.
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

      {/* Filter and Layer Bar */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-3">
        {/* Layer Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span>Map Geospatial Layers:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowFacilities(!showFacilities)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                showFacilities
                  ? 'bg-blue-500/20 text-blue-300 border-blue-500/40 shadow-sm'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Hospitals & PHCs</span>
            </button>

            <button
              onClick={() => setShowWarehouses(!showWarehouses)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                showWarehouses
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <Boxes className="w-3.5 h-3.5" />
              <span>Warehouses & MSDs</span>
            </button>

            <button
              onClick={() => setShowDiseaseHeatmap(!showDiseaseHeatmap)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                showDiseaseHeatmap
                  ? 'bg-orange-500/20 text-orange-300 border-orange-500/40 shadow-sm'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-orange-400" />
              <span>Disease Heatmap</span>
            </button>

            <button
              onClick={() => setShowEmergencyHeatmap(!showEmergencyHeatmap)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                showEmergencyHeatmap
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-sm'
                  : 'bg-slate-950 text-slate-500 border-slate-800'
              }`}
            >
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>Emergency Heatmap</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[200px]">
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
              onChange={(e) => {
                setSelectedState(e.target.value);
                setSelectedDistrict('All');
              }}
              className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
            >
              {states.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* District Filter (REQUIRED BY PHASE 4) */}
          <div className="flex items-center gap-1.5">
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

          {/* Facility Type Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Type:</span>
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

          {/* Risk Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Risk:</span>
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

          {/* Reset Filters */}
          <button
            onClick={() => {
              setSelectedState('All');
              setSelectedDistrict('All');
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
          <span className="font-semibold text-slate-300">Markers & Layers Legend:</span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Low Risk
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> Moderate
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 inline-block" /> High Shortage
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block animate-pulse" /> Critical Outbreak
          </span>
          <span className="flex items-center gap-1.5 text-amber-300">
            <Boxes className="w-3.5 h-3.5" /> Warehouse Depot
          </span>
          {showDiseaseHeatmap && (
            <span className="flex items-center gap-1.5 text-orange-400 font-semibold">
              <span className="w-3 h-3 rounded-full bg-orange-500/30 border border-orange-500 inline-block" /> Disease Surveillance Zone
            </span>
          )}
          {showEmergencyHeatmap && (
            <span className="flex items-center gap-1.5 text-rose-400 font-semibold">
              <span className="w-3 h-3 rounded-full bg-rose-500/40 border border-rose-500 inline-block" /> Defcon Crisis Zone
            </span>
          )}
        </div>
      </Card>

      {/* Map Viewport Container */}
      <div className="h-[620px] w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative">
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

          {/* Disease Heatmap Circles Layer */}
          {showDiseaseHeatmap &&
            mockDiseaseHotspots.map((hotspot) => (
              <Circle
                key={hotspot.id}
                center={[hotspot.lat, hotspot.lng]}
                radius={hotspot.radiusMeters}
                pathOptions={{
                  fillColor: '#f97316',
                  fillOpacity: 0.25,
                  color: '#ea580c',
                  weight: 2,
                  dashArray: '4, 4',
                }}
              >
                <Popup>
                  <div className="p-1 space-y-1.5 min-w-[200px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400">
                        Disease Hotspot
                      </span>
                      <Badge level={hotspot.severity}>{hotspot.severity.toUpperCase()}</Badge>
                    </div>
                    <h4 className="font-bold text-xs text-white">{hotspot.name}</h4>
                    <p className="text-[11px] text-slate-300">
                      Surveillance: <strong className="text-orange-300">{hotspot.disease}</strong>
                    </p>
                    <p className="text-[10px] text-slate-400">
                      Reported Cases this week: <strong className="text-slate-100 font-mono">{hotspot.caseCount}</strong>
                    </p>
                  </div>
                </Popup>
              </Circle>
            ))}

          {/* Emergency Crisis Heatmap Circles Layer */}
          {showEmergencyHeatmap &&
            mockEmergencyHotspots.map((crisis) => (
              <Circle
                key={crisis.id}
                center={[crisis.lat, crisis.lng]}
                radius={crisis.radiusMeters}
                pathOptions={{
                  fillColor: '#ef4444',
                  fillOpacity: 0.35,
                  color: '#dc2626',
                  weight: 3,
                }}
              >
                <Popup>
                  <div className="p-1 space-y-1.5 min-w-[210px]">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">
                        DEFCON Emergency Zone
                      </span>
                      <Badge level="critical">CRITICAL</Badge>
                    </div>
                    <h4 className="font-bold text-xs text-white">{crisis.name}</h4>
                    <p className="text-[11px] text-rose-300 font-semibold">{crisis.alert}</p>
                    <p className="text-[10px] text-slate-400">
                      Immediate inter-district logistics reallocation required.
                    </p>
                  </div>
                </Popup>
              </Circle>
            ))}

          {/* Facility & Warehouse Markers */}
          {filteredFacilities.map((facility: FacilityMapItem) => {
            const colors = riskColors[facility.risk_level];
            const isWarehouse = facility.type === 'Warehouse';

            return (
              <CircleMarker
                key={facility.id}
                center={[facility.latitude, facility.longitude]}
                radius={
                  isWarehouse
                    ? 13
                    : facility.risk_level === 'critical'
                    ? 14
                    : facility.risk_level === 'high'
                    ? 11
                    : 9
                }
                pathOptions={{
                  fillColor: isWarehouse ? '#f59e0b' : colors.fill,
                  fillOpacity: isWarehouse ? 0.9 : 0.85,
                  color: isWarehouse ? '#fbbf24' : colors.stroke,
                  weight: isWarehouse ? 3 : 2,
                }}
              >
                <Popup>
                  <div className="p-1 space-y-2 min-w-[250px]">
                    <div className="flex items-start justify-between gap-2 border-b border-slate-700/60 pb-1.5">
                      <div>
                        <div className="flex items-center gap-1.5">
                          {isWarehouse && <Boxes className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                          <h4 className="font-bold text-xs text-white leading-tight">
                            {facility.name}
                          </h4>
                        </div>
                        <span className="text-[10px] text-slate-400">
                          {facility.district}, {facility.state} • <span className="font-mono text-cyan-400">{facility.id}</span>
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
                      <span className="text-teal-400 font-mono font-bold">{facility.type}</span>
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
