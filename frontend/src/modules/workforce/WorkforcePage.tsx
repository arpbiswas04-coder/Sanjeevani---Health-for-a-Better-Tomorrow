import { OperationsActions } from '@/modules/equipment/OperationsActions';
import { useLocation } from 'react-router-dom';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
export const WorkforcePage: React.FC = () => {
 const location = useLocation(); const [selected,setSelected]=useState<any>(null);
 const [facility,setFacility]=useFacilitySelection(); const [tab,setTab]=useState(location.pathname.endsWith('/attendance') ? 'attendance' : 'staff');
 const columns:Record<string,{key:string;label:string}[]>={staff:[{key:'display_name',label:'Name'},{key:'code',label:'Code'},{key:'staff_role_id',label:'Staff role ID'},{key:'active',label:'Active'}],shifts:[{key:'staff_id',label:'Staff ID'},{key:'starts_at',label:'Starts at'},{key:'ends_at',label:'Ends at'},{key:'cancelled',label:'Cancelled'}],attendance:[{key:'staff_id',label:'Staff ID'},{key:'day',label:'Day'},{key:'status',label:'Status'}]};
 return <div className="space-y-6"><PageHeading title="Workforce Telemetry, Personnel Management & Attendance" description="Backend personnel, shift and attendance records. Attendance status does not imply biometric verification." /><Card><FacilityPicker value={facility} onChange={id=>{setFacility(id);setSelected(null);}}/></Card>
 <div className="flex flex-wrap gap-2">{[['staff','Personnel Directory'],['shifts','Shift Roster'],['attendance','Attendance'],['ratios','Ratios & Load']].map(([id,label])=><button key={id} className={buttonClass} aria-pressed={tab===id} onClick={()=>{setTab(id);setSelected(null);}}>{label}</button>)}</div>
 <OperationsActions key={`${facility}-${tab}`} kind={tab} facility={facility} selected={selected}/>
 {tab==='ratios'?<Unavailable>Doctor-to-patient ratios, department workload, biometric verification and emergency paging are not supplied by the backend.</Unavailable>:<DataPanel key={`${facility}-${tab}`} title={tab==='staff'?'Personnel Directory':tab==='shifts'?'Shift Roster':'Attendance Records'} path={`/operations/${tab}`} params={{facility_id:facility}} permission="workforce.read" enabled={!!facility} columns={columns[tab]} onSelect={setSelected}/>}
 <DataPanel title="Staff role catalogue" path="/staff-roles" permission="workforce.read" columns={[{key:'id',label:'Role ID'},{key:'name',label:'Role'}]}/></div>;
};
export default WorkforcePage;
