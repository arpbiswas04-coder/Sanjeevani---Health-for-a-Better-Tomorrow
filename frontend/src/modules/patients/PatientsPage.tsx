import { OperationsActions } from '@/modules/equipment/OperationsActions';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataPanel, Unavailable } from '@/components/common/BackendData';
export const PatientsPage: React.FC = () => {
 const [facility,setFacility]=useFacilitySelection(); const [selected,setSelected]=useState<any>(null);
 return <div className="space-y-6"><PageHeading title="Patient Footfall & Clinical Load" description="Recorded daily patient aggregates by category; no individual patient records are exposed."/><Card><FacilityPicker value={facility} onChange={id=>{setFacility(id);setSelected(null);}}/></Card><OperationsActions key={`actions-${facility}`} kind="footfall" facility={facility} selected={selected}/><DataPanel key={facility} title="Patient footfall" path="/operations/footfall" params={{facility_id:facility}} permission="integration.read" enabled={!!facility} onSelect={setSelected} columns={[{key:'day',label:'Day'},{key:'category',label:'Category'},{key:'count',label:'Count'},{key:'updated_at',label:'Updated at'}]}/><Unavailable>Hourly admission/discharge curves, triage queues and waiting times have no backend source.</Unavailable></div>;
};
export default PatientsPage;
