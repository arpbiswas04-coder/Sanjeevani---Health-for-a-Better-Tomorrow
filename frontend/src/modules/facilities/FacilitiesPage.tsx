import { FacilityActions } from './FacilityActions';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, MapPin } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useFacilityDirectory } from '@/hooks/useFacilityDirectory';
import { buttonClass, controlClass, DataState, DetailPanel, PageHeading } from '@/components/common/BackendData';

export const FacilitiesPage: React.FC = () => {
  const [search, setSearch] = useState(''); const [type, setType] = useState('');
  const [state, setState] = useState(''); const [district, setDistrict] = useState(''); const [block, setBlock] = useState('');
  const [active, setActive] = useState(true); const [detail, setDetail] = useState('');
  const directory = useFacilityDirectory({ active, state_id: state, district_id: district, block_id: block });
  const query = directory.facilities;
  const rows = (query.data || []).filter(f => (!type || f.facility_type === type) && `${f.name} ${f.code} ${f.address || ''}`.toLowerCase().includes(search.toLowerCase()));
  return <div className="space-y-6 animate-in fade-in duration-300">
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4"><PageHeading title="Facilities, Hospitals & Medical Depots" description="Healthcare Infrastructure Directory - backend records in your permitted scope." /><Link to="/map" className={buttonClass}><MapPin className="inline w-4 h-4" /> Switch to Geospatial Map</Link></div>
    <FacilityActions selected={query.data?.find(f=>f.id===detail)}/>
    <Card className="p-4 flex flex-wrap gap-3 items-center">
      <input aria-label="Search facilities" placeholder="Search facility name, code, or address..." className={controlClass} value={search} onChange={e => setSearch(e.target.value)} />
      <select aria-label="Facility type" className={controlClass} value={type} onChange={e => setType(e.target.value)}><option value="">All types</option>{Array.from(new Set(query.data?.map(f => f.facility_type))).map(t => <option key={t}>{t}</option>)}</select>
      <select aria-label="Facility status" className={controlClass} value={String(active)} onChange={e => { setActive(e.target.value === 'true'); setDetail(''); }}><option value="true">Active</option><option value="false">Inactive</option></select>
      <select aria-label="State" className={controlClass} value={state} onChange={e => { setState(e.target.value); setDistrict(''); setBlock(''); }}><option value="">All states</option>{directory.states.data?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
      <select aria-label="District" className={controlClass} value={district} onChange={e => { setDistrict(e.target.value); setBlock(''); }}><option value="">All districts</option>{directory.districts.data?.filter(d => !state || d.state_id === state).map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
      <select aria-label="Block" className={controlClass} value={block} onChange={e => setBlock(e.target.value)}><option value="">All blocks</option>{directory.blocks.data?.filter(b => !district || b.district_id === district).map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select>
      <button className={buttonClass} disabled={query.isFetching} onClick={() => query.refetch()}>Refresh facilities</button>
      {query.data && <span className="text-xs text-slate-400">Total: {rows.length} facilities</span>}
    </Card>
    {[directory.countries, directory.states, directory.districts, directory.blocks].map((q, index) => q.error ? <DataState key={index} query={q}>{null}</DataState> : null)}
    <DataState query={query} empty={rows.length === 0}><div className="grid grid-cols-1 md:grid-cols-2 gap-5">{rows.map(f => {
      const place = directory.location(f);
      return <Card key={f.id} className="flex flex-col justify-between space-y-4 hover:border-slate-600">
        <div className="flex gap-3 border-b border-slate-800 pb-3"><Building2 className="w-5 h-5 text-blue-400" /><div><h3 className="font-bold text-sm text-slate-100">{f.name}</h3><p className="text-xs text-slate-400">{directory.geographyPending ? 'Loading geography...' : directory.geographyUnavailable ? 'Geography unavailable' : [place.block?.name, place.district?.name, place.state?.name, place.country?.name].filter(Boolean).join(', ') || 'Geography not recorded'} / {f.facility_type}</p></div><span className="ml-auto text-xs text-teal-400">{f.active ? 'Active' : 'Inactive'}</span></div>
        <div className="grid grid-cols-3 gap-2 text-xs"><div>Code<p className="text-slate-200">{f.code}</p></div><div>Contact<p className="text-slate-200">{f.contact || 'Not recorded'}</p></div><div>Coordinates<p className="text-slate-200">{f.latitude !== null && f.longitude !== null ? `${f.latitude}, ${f.longitude}` : 'Not recorded'}</p></div></div>
        <p className="text-xs text-slate-400">{f.address || 'Address not recorded'}</p>
        {f.location_context && <p className="text-xs text-amber-300">Map reference: approximate city point for {f.location_context.city}, {f.location_context.state}; not hospital coordinates.</p>}
        <div className="flex justify-between border-t border-slate-800 pt-3"><button className={buttonClass} onClick={() => setDetail(f.id)}>View {f.name} details</button><Link className={buttonClass} to={`/inventory?facility_id=${encodeURIComponent(f.id)}`}>View Stock Ledger</Link></div>
      </Card>;
    })}</div></DataState>
    {detail && <DetailPanel key={detail} title="Facility details" path={`/facilities/${detail}`} permission="inventory.read" />}
  </div>;
};
export default FacilitiesPage;
