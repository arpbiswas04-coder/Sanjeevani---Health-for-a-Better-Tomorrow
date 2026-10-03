import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { DataPanel, DetailPanel, controlClass } from '@/components/common/BackendData';

export function OperationalContext() {
  const [facility, setFacility] = useFacilitySelection(); const [district, setDistrict] = useState('');
  const [medicine, setMedicine] = useState('');
  return <div className="space-y-5"><Card className="flex flex-wrap gap-3"><FacilityPicker value={facility} onChange={setFacility} /><input aria-label="Context district ID" placeholder="District ID for population" className={controlClass} value={district} onChange={e => setDistrict(e.target.value)} /><input aria-label="Context medicine ID" placeholder="Medicine ID for stock context" className={controlClass} value={medicine} onChange={e => setMedicine(e.target.value)} /></Card>
    {facility && <DetailPanel key={facility} title="Facility weather" path={`/integrations/weather/${facility}`} permission="integration.read" />}
    <DataPanel key={district} title="Population source records" path="/integrations/population" params={{district_id:district}} permission="integration.read" enabled={!!district} columns={[{key:'population',label:'Population'},{key:'source',label:'Source'},{key:'source_url',label:'Source URL'},{key:'as_of',label:'As of'},{key:'retrieved_at',label:'Retrieved at'}]} />
    {facility && medicine && <OptimizationContext facility={facility} medicine={medicine} />}
  </div>;
}
import { useBackendData } from '@/hooks/useBackendData';
import { DataState, Fields } from '@/components/common/BackendData';
function OptimizationContext({ facility, medicine }: { facility: string; medicine: string }) {
  const query = useBackendData<object>('/optimization/context', {facility_id:facility,medicine_id:medicine}, 'integration.read');
  return <Card className="space-y-3"><h3 className="text-sm font-bold">Optimization input context</h3><p className="text-xs text-slate-400">Null predicted demand or transport metadata means no value is available; it is never replaced by a forecast.</p><DataState query={query}>{query.data && <Fields value={query.data} />}</DataState></Card>;
}
