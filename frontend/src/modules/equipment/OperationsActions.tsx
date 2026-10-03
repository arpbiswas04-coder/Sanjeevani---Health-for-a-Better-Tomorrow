import { MutationForm, Values, Options } from '@/components/common/MutationForm';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { DataState } from '@/components/common/BackendData';

export function OperationsActions({kind,facility,selected}:{kind:string;facility:string;selected?:Values|null}) {
 const workforce=['staff','shifts','attendance'].includes(kind), asset=['equipment','ambulances'].includes(kind);
 const permission=workforce?'workforce.write':asset?'equipment.write':kind==='beds'?'beds.write':'integration.write';
 const allowed=useCapability(permission);
 const roles=useBackendData<Values[]>('/staff-roles',{},'workforce.read',allowed&&kind==='staff',true);
 const staff=useBackendData<Values[]>('/operations/staff',{facility_id:facility},'workforce.read',allowed&&['shifts','attendance'].includes(kind)&&!!facility,true);
 if(!facility||!allowed)return null;
 const fixed={facility_id:facility};
 const options:Options={staff_role_id:(roles.data||[]).map(r=>({value:r.id,label:r.name})),staff_id:(staff.data||[]).filter(r=>r.active).map(r=>({value:r.id,label:`${r.display_name} (${r.code})`}))};
 const validBeds=(b:Values)=>b.occupied>b.capacity?'Occupancy exceeds capacity.':undefined;
 const validAsset=(b:Values)=>(b.latitude==null)!==(b.longitude==null)?'Provide both coordinates.':!b.operational&&b.status==='available'?'Non-operational ambulances cannot be available.':undefined;
 return <div className="flex flex-wrap gap-2">
 {kind==='beds'&&<MutationForm key={selected?.id || 'new'} title="Update bed capacity" path="/beds" method="PUT" schema="BedInput" permission={permission} fixed={fixed} defaults={selected||{}} validate={validBeds} confirm="Replace recorded capacity and occupied count for this facility and bed type. This does not reserve individual beds."/>}
 {asset&&<><MutationForm title={`Register ${kind==='equipment'?'equipment':'ambulance'}`} path={`/${kind}`} schema={kind==='equipment'?'EquipmentInput':'AmbulanceInput'} permission={permission} fixed={fixed} validate={kind==='ambulances'?validAsset:undefined}/>
 {selected&&<MutationForm key={selected.id} title={`Edit ${kind==='equipment'?'equipment':'ambulance'}`} path={`/${kind}/${selected.id}`} method="PUT" schema={kind==='equipment'?'EquipmentInput':'AmbulanceInput'} permission={permission} fixed={fixed} defaults={selected} validate={kind==='ambulances'?validAsset:undefined} confirm="Save this asset's recorded status and operational details. This does not dispatch a vehicle."/>}
 {selected&&kind==='equipment'&&<MutationForm title="Record maintenance" path={`/equipment/${selected.id}/maintenance`} schema="MaintenanceInput" permission={permission} validate={b=>b.next_due<=b.performed_on||b.performed_on>new Date().toISOString().slice(0,10)?'Performed date must be today or earlier (UTC); next due must be later.':undefined}/>}</>}
 {kind==='staff'&&<><DataState query={roles}>{null}</DataState><MutationForm title="Add staff role" path="/staff-roles" schema="StaffRoleInput" permission={permission} global/>{roles.data&&<><MutationForm title="Add staff" path="/staff" schema="StaffInput" permission={permission} fixed={fixed} options={options}/>{selected&&<MutationForm key={selected.id} title="Edit staff" path={`/staff/${selected.id}`} method="PUT" schema="StaffInput" permission={permission} fixed={fixed} defaults={selected} options={options} confirm="Save staff details and active state. Future operations will use the updated record."/>}</>}</>}
 {kind==='shifts'&&staff.data&&<><MutationForm title="Create shift" path="/shifts" schema="ShiftInput" permission={permission} options={options} validate={b=>{const duration=Date.parse(b.ends_at)-Date.parse(b.starts_at);return duration<=0||duration>86400000?'Shift must be longer than zero and no more than 24 hours.':undefined;}}/>{selected&&!selected.cancelled&&<MutationForm title="Cancel shift" path={`/shifts/${selected.id}/cancel`} permission={permission} confirm={`Cancel shift for ${selected.staff_id}, ${selected.starts_at} to ${selected.ends_at}.`}/>}</>}
 {kind==='attendance'&&staff.data&&<MutationForm title="Record attendance" path="/attendance" schema="AttendanceInput" permission={permission} options={options}/>}
 {['footfall','disease-counts'].includes(kind)&&<MutationForm key={selected?.id||'new'} title={`Record ${kind==='footfall'?'footfall':'disease count'}`} path={`/aggregates/${kind}`} method="PUT" schema="AggregateInput" permission={permission} fixed={fixed} defaults={selected?{...selected,expected_version:selected.version}:{}} confirm="Save the daily aggregate. For an existing record, the expected version must match; conflicting updates are rejected."/>}
 </div>;
}
