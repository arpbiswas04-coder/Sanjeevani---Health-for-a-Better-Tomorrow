import React, { useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { Card } from '@/components/ui/Card';
import { useFacilityDirectory } from '@/hooks/useFacilityDirectory';
import { PageHeading, DataState, Unavailable, controlClass, buttonClass } from '@/components/common/BackendData';

export const InteractiveResourceMap: React.FC = () => {
  const [state, setState] = useState(''); const [district, setDistrict] = useState('');
  const [search, setSearch] = useState(''); const [type, setType] = useState('');
  const [warehouses, setWarehouses] = useState(true); const [facilities, setFacilities] = useState(true);
  const directory = useFacilityDirectory({ active: true });
  const query = directory.facilities;
  // Approximate state labels are display filters only; backend jurisdiction and
  // authorization still use the real hierarchy, never these reference points.
  const selectedState = directory.states.data?.find(s => s.id === state)?.name;
  const rows = (query.data || []).filter(f => (!state || directory.location(f).state?.id === state || (!!selectedState && f.location_context?.state === selectedState)) && (!district || directory.location(f).district?.id === district) && (!type || f.facility_type === type) && f.name.toLowerCase().includes(search.toLowerCase()) && (f.facility_type.toLowerCase() === 'warehouse' ? warehouses : facilities));
  const plotted = rows.flatMap(f => {
    if (Number.isFinite(f.latitude) && Number.isFinite(f.longitude)) return [{ facility: f, latitude: f.latitude!, longitude: f.longitude!, approximate: false }];
    const point = f.location_context;
    return point?.precision === 'approximate_city' && Number.isFinite(point.latitude) && Number.isFinite(point.longitude)
      ? [{ facility: f, latitude: point.latitude, longitude: point.longitude, approximate: true }] : [];
  });
  const groups = new Map<string, typeof plotted>();
  for (const point of plotted) {
    const key = `${point.latitude},${point.longitude},${point.approximate},${point.facility.facility_type}`;
    groups.set(key, [...(groups.get(key) || []), point]);
  }
  return <div className="space-y-5 animate-in fade-in duration-300">
    <PageHeading title="Geospatial Healthcare Network Telemetry" description="Recorded facility points and explicitly approximate city references. City references are not hospital locations, travel distances or jurisdiction assignments." />
    <Card className="p-4 space-y-3"><div className="flex flex-wrap gap-2">
      <button className={buttonClass} aria-pressed={facilities} onClick={() => setFacilities(!facilities)}>Hospitals & PHCs</button><button className={buttonClass} aria-pressed={warehouses} onClick={() => setWarehouses(!warehouses)}>Warehouses & MSDs</button>
      <button className={buttonClass} disabled>Disease Heatmap - unavailable</button><button className={buttonClass} disabled>Emergency Heatmap - unavailable</button></div>
      <div className="flex flex-wrap gap-3"><input className={controlClass} aria-label="Search map facilities" placeholder="Search facility name..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className={controlClass} aria-label="State" value={state} onChange={e => { setState(e.target.value); setDistrict(''); }}><option value="">All states</option>{directory.states.data?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
        <select className={controlClass} aria-label="District" value={district} onChange={e => setDistrict(e.target.value)}><option value="">All districts</option>{directory.districts.data?.filter(d => !state || d.state_id === state).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
        <select className={controlClass} aria-label="Type" value={type} onChange={e => setType(e.target.value)}><option value="">All types</option>{Array.from(new Set(query.data?.map(f => f.facility_type))).map(t => <option key={t}>{t}</option>)}</select>
        <button className={buttonClass} onClick={() => query.refetch()}>Refresh map</button></div>
      {query.data && <p className="text-xs text-slate-400">Nodes visible: {plotted.length} / {rows.length - plotted.length} facilities without coordinates. Blue: healthcare facility; amber: warehouse.</p>}
      {query.data && <p className="text-xs text-slate-400">{plotted.filter(p => p.approximate).length} approximate city references (dashed markers). Shared city points are grouped without adding random offsets. State filters include reviewed city-state labels; district filters require an actual assigned district.</p>}
    </Card>
    {[directory.countries, directory.states, directory.districts, directory.blocks].map((q, i) => q.error ? <DataState key={i} query={q}>{null}</DataState> : null)}
    <DataState query={query} empty={!rows.length}>
      <div className="h-[620px] w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl relative"><MapContainer center={[22.5, 80.5]} zoom={5} scrollWheelZoom className="h-full w-full">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
        {Array.from(groups.entries()).map(([key, points]) => <CircleMarker key={key} center={[points[0].latitude, points[0].longitude]} radius={9} pathOptions={{ color: points[0].facility.facility_type.toLowerCase() === 'warehouse' ? '#f59e0b' : '#38bdf8', dashArray: points[0].approximate ? '4 4' : undefined }}><Popup><div className="space-y-3 max-h-72 overflow-y-auto">{points.map(({ facility: f, approximate }) => <div key={f.id} className="space-y-2"><strong>{f.name}</strong><p>{f.facility_type} / {f.code}</p><p>{f.address || 'Address not recorded'}</p>{approximate ? <><p>Approximate city reference: {f.location_context!.city}, {f.location_context!.state}. Not the hospital location.</p><p>{f.location_context!.attribution} · reference {f.location_context!.reference_id}</p></> : <p>Recorded facility coordinates; accuracy is not independently verified.</p>}<p>{directory.geographyPending ? 'Loading geography...' : directory.geographyUnavailable ? 'Geography unavailable' : Object.values(directory.location(f)).map(v => v?.name).filter(Boolean).join(', ') || 'Geography not recorded'}</p><p>{f.contact || 'Contact not recorded'}</p></div>)}</div></Popup></CircleMarker>)}
      </MapContainer></div>
    </DataState>
    <Unavailable>Disease and crisis polygons, facility risk scores and oxygen runway have no matching backend data source.</Unavailable>
  </div>;
};
export default InteractiveResourceMap;
