import { OperationsActions } from '@/modules/equipment/OperationsActions';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataPanel, Unavailable } from '@/components/common/BackendData';
export const DiseasePage: React.FC = () => {
 const [facility,setFacility]=useFacilitySelection(); const [selected,setSelected]=useState<any>(null);
 return <div className="space-y-6"><PageHeading title="Disease Surveillance & Epidemiological Signals" description="Recorded disease-count aggregates for the selected facility."/><Card><FacilityPicker value={facility} onChange={id=>{setFacility(id);setSelected(null);}}/></Card><OperationsActions key={`actions-${facility}`} kind="disease-counts" facility={facility} selected={selected}/><DataPanel key={facility} title="Disease counts" path="/operations/disease-counts" params={{facility_id:facility}} permission="integration.read" enabled={!!facility} onSelect={setSelected} columns={[{key:'day',label:'Day'},{key:'category',label:'Disease category'},{key:'count',label:'Count'},{key:'updated_at',label:'Updated at'}]}/><Unavailable>Outbreak severity predictions, hotspot boundaries and percentage growth metrics are not returned by this API.</Unavailable></div>;
};
export default DiseasePage;
