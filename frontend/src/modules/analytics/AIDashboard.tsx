import { OperationalContext } from './OperationalContext';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { PageHeading, DataPanel, Unavailable, buttonClass, controlClass } from '@/components/common/BackendData';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { ReportsPanel } from './ReportsPanel';
export const AIDashboard: React.FC = () => {
 const [tab,setTab]=useState('reports'); const [facility,setFacility]=useFacilitySelection(); const [medicine,setMedicine]=useState(''); const [start,setStart]=useState(''); const [end,setEnd]=useState('');
 return <div className="space-y-6"><PageHeading title="Analytics, Predictive AI & Supply Chain Resilience" description="Backend reports, recorded consumption and submitted optimization recommendations. Unsupported predictions remain unavailable."/>
 <div className="flex flex-wrap gap-2">{[['reports','Reports & Downloads'],['trends','Historical Trend & Utilization'],['recommendations','Optimization Recommendations'],['context','Weather, Population & Stock Context'],['forecasting','Demand Forecasting'],['cost','Cost & Wastage Reduction'],['resilience','Resilience & Risk Scores'],['comparison','District Comparison & Benchmarking']].map(([id,label])=><button key={id} className={buttonClass} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
 {tab==='reports'&&<ReportsPanel/>}
 {tab==='context'&&<OperationalContext/>}
 {tab==='trends'&&<><Card className="flex flex-wrap gap-3"><FacilityPicker value={facility} onChange={setFacility}/><input className={controlClass} aria-label="Consumption medicine ID" placeholder="Medicine ID" value={medicine} onChange={e=>setMedicine(e.target.value)}/><label className="text-xs">Start<input className={controlClass} aria-label="Consumption start date" type="date" value={start} onChange={e=>setStart(e.target.value)}/></label><label className="text-xs">End<input className={controlClass} aria-label="Consumption end date" type="date" value={end} onChange={e=>setEnd(e.target.value)}/></label></Card><DataPanel key={`${facility}-${medicine}-${start}-${end}`} title="Recorded medicine consumption" path="/datasets/medicine-consumption" params={{facility_id:facility,medicine_id:medicine,start_date:start,end_date:end}} permission="integration.read" enabled={!!facility&&!!medicine&&!!start&&!!end} columns={[{key:'day',label:'Day'},{key:'consumed',label:'Consumed'}]}/></>}
 {tab==='recommendations'&&<DataPanel title="Submitted optimization recommendations" path="/optimization/recommendations" permission="integration.read" columns={[{key:'source_id',label:'Source ID'},{key:'destination_id',label:'Destination ID'},{key:'status',label:'Status'},{key:'model_version',label:'Model version'},{key:'payload',label:'Submitted recommendation'}]}/>}
 {['forecasting','cost','resilience','comparison'].includes(tab)&&<Card><Unavailable>{tab==='forecasting'?'Demand forecasts, stockout probabilities and SHAP attribution':tab==='cost'?'Monetary wastage prevented and cost savings':tab==='resilience'?'Supply chain resilience scores and predicted risk':'District performance benchmarks'} have no working endpoint in the configured backend. No demonstration values are shown.</Unavailable></Card>}
 </div>;
};
export default AIDashboard;
