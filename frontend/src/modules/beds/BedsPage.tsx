import { OperationsActions } from '@/modules/equipment/OperationsActions';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataState, DataPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
import { useBackendData } from '@/hooks/useBackendData';
import { BedsAvailable } from '@/services/backendTypes';
export const BedsPage: React.FC = () => {
 const [facility,setFacility]=useFacilitySelection(); const [bed,setBed]=useState('');
 const query=useBackendData<BedsAvailable[]>('/operations/beds',{facility_id:facility},'beds.read',!!facility,true);
 return <div className="space-y-6"><PageHeading title="Real-Time Bed Availability & Ventilator Occupancy" description="Recorded capacity and occupancy for the selected facility; refresh to retrieve current backend values." />
 <Card><FacilityPicker value={facility} onChange={id=>{setFacility(id);setBed('');}} /><button className={buttonClass} disabled={!facility || query.isFetching} onClick={()=>query.refetch()}>Refresh beds</button></Card>
 <OperationsActions key={facility} kind="beds" facility={facility} selected={query.data?.find(b=>b.id===bed)}/>
 <DataState query={query} empty={!query.data?.length}><div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">{query.data?.map(b=><Card key={b.id} className="space-y-3"><h3 className="text-sm text-purple-300">{b.bed_type}</h3><p className="text-2xl font-bold">{b.available} available</p><p className="text-xs text-slate-400">{b.occupied} occupied / {b.capacity} capacity</p><p className="text-xs">{b.capacity ? `${(100*b.occupied/b.capacity).toFixed(1)}% occupied` : 'Occupancy percentage unavailable: zero capacity'}</p><button className={buttonClass} onClick={()=>setBed(b.id)}>View history</button></Card>)}</div></DataState>
 {bed && <DataPanel key={bed} title="Bed occupancy history" path={`/beds/${bed}/history`} permission="beds.read" columns={[{key:'created_at',label:'Recorded at'},{key:'capacity',label:'Capacity'},{key:'occupied',label:'Occupied'},{key:'actor_id',label:'Actor ID'}]} />}
 <Unavailable>Individual bed reservation and patient allocation have no backend endpoint. No reservation is simulated.</Unavailable></div>;
};
export default BedsPage;
