import { useState } from 'react';
import { MutationForm, Values } from '@/components/common/MutationForm';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { controlClass, DataState } from '@/components/common/BackendData';

export function FacilityActions({selected}:{selected?:Values}) {
 const [kind,setKind]=useState('countries'); const global=useCapability('facility.manage',true);
 const manage=useCapability('facility.manage');
 const parent: string|undefined=({states:'countries',districts:'states',blocks:'districts'} as Record<string,string>)[kind];
 const geography=useBackendData<Values[]>(`/geography/${parent||'blocks'}`,{},'inventory.read',!!parent&&global,true);
 const blocks=useBackendData<Values[]>('/geography/blocks',{},'inventory.read',!!selected&&manage,true);
 return <div className="space-y-3"><div className="flex flex-wrap gap-2"><MutationForm title="Create facility" path="/facilities" schema="FacilityCreate" permission="facility.manage" global/>
 {selected&&<MutationForm key={selected.id} title="Edit facility" path={`/facilities/${selected.id}`} method="PATCH" schema="FacilityUpdate" permission="facility.manage" defaults={selected} options={{block_id:(blocks.data||[]).map(r=>({value:r.id,label:r.name}))}} confirm={`Save metadata and active state for ${selected.name}. Deactivation affects new operational transactions.`} validate={b=>(b.latitude==null)!==(b.longitude==null)?'Provide both coordinates.':undefined}/>}</div>
 {global&&<div className="flex flex-wrap gap-2"><label className="text-xs">Geography level <select aria-label="Geography level" value={kind} onChange={e=>setKind(e.target.value)} className={controlClass}>{['countries','states','districts','blocks'].map(k=><option key={k}>{k}</option>)}</select></label>{parent&&<DataState query={geography}>{null}</DataState>}{(!parent||geography.data)&&<MutationForm key={kind} title="Add geography" path={`/geography/${kind}`} schema="GeographyCreate" permission="facility.manage" global fixed={!parent?{parent_id:null}:undefined} options={{parent_id:(geography.data||[]).map(r=>({value:r.id,label:r.name}))}} validate={b=>parent&&!b.parent_id?'Select the parent geography.':undefined}/>}</div>}</div>;
}
