import { OperationsActions } from './OperationsActions';
import { useLocation } from 'react-router-dom';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
export const EquipmentPage: React.FC = () => {
 const location = useLocation();
 const [facility,setFacility]=useFacilitySelection(); const [tab,setTab]=useState(location.pathname.endsWith('/ambulance') ? 'ambulances' : 'equipment'); const [equipment,setEquipment]=useState(''); const [selected,setSelected]=useState<any>(null);
 return <div className="space-y-6"><PageHeading title="Biomedical Equipment & Ambulance Fleet Telemetry" description="Recorded equipment status, maintenance dates and ambulance availability."/><Card><FacilityPicker value={facility} onChange={id=>{setFacility(id);setEquipment('');setSelected(null);}}/></Card>
 <div className="flex gap-2">{['equipment','ambulances'].map(t=><button key={t} className={buttonClass} aria-pressed={tab===t} onClick={()=>{setTab(t);setEquipment('');setSelected(null);}}>{t==='equipment'?'Biomedical Equipment':'Ambulance Fleet'}</button>)}</div>
 <OperationsActions key={`actions-${facility}-${tab}`} kind={tab} facility={facility} selected={selected}/>
 <DataPanel key={`${facility}-${tab}`} title={tab==='equipment'?'Equipment register':'Ambulance register'} path={`/assets/${tab}`} params={{facility_id:facility}} permission="equipment.read" enabled={!!facility} columns={tab==='equipment'?[{key:'code',label:'Code'},{key:'equipment_type',label:'Type'},{key:'status',label:'Status'},{key:'last_maintenance',label:'Last maintenance'},{key:'next_maintenance',label:'Next maintenance'},{key:'notes',label:'Notes'}]:[{key:'vehicle_id',label:'Vehicle'},{key:'status',label:'Status'},{key:'operational',label:'Operational'},{key:'latitude',label:'Latitude'},{key:'longitude',label:'Longitude'}]} onSelect={row=>{setSelected(row);if(tab==='equipment')setEquipment(String(row.id));}}/>
 {equipment && <DataPanel key={equipment} title="Maintenance history" path={`/equipment/${equipment}/maintenance`} permission="equipment.read" columns={[{key:'performed_on',label:'Performed on'},{key:'next_due',label:'Next due'},{key:'notes',label:'Notes'},{key:'actor_id',label:'Actor ID'}]}/>}
 <Unavailable>Uptime percentages, ambulance ETA, crew and oxygen telemetry are not provided. Asset records and maintenance can be updated by authorized users; vehicle dispatch has no dedicated workflow contract.</Unavailable></div>;
};
export default EquipmentPage;
