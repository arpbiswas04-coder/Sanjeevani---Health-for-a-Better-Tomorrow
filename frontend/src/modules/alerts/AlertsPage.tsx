import { MutationForm } from '@/components/common/MutationForm';
import React, { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { PageHeading, DataState, DataError, DataPanel, Fields, controlClass, buttonClass } from '@/components/common/BackendData';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { sendData } from '@/services/dataApi';
import { AlertView } from '@/services/backendTypes';
export const AlertsPage: React.FC = () => {
 const [tab,setTab]=useState('alerts'); const [status,setStatus]=useState(''); const [severity,setSeverity]=useState('');
 const [selected,setSelected]=useState(''); const [busy,setBusy]=useState(''); const [error,setError]=useState<Error|null>(null);
 const query=useBackendData<AlertView[]>('/alerts',{},'alerts.read',true,true); const manage=useCapability('alerts.manage'); const cache=useQueryClient();
 const rows=(query.data||[]).filter(a=>(!status||a.status===status)&&(!severity||a.severity===severity));
 const submission=useRef(false);
 async function acknowledge(id:string) {if(submission.current)return;submission.current=true;setBusy(id);setError(null);try {await sendData(`/alerts/${id}/actions`,'POST',{status:'acknowledged'});await cache.invalidateQueries({queryKey:['backend']});}catch(e){setError(e instanceof Error?e:new Error('Acknowledgement failed.'));}finally{submission.current=false;setBusy('');}}
 return <div className="space-y-6"><PageHeading title="Emergency Alert Management & Threshold Rules" description="Backend incidents, configured thresholds and escalation records in your permitted scope."/>
 <div className="flex flex-wrap gap-2">{[['alerts','Incident Feed'],['rules','Threshold Engine'],['notifications','Notifications'],['escalations','Escalation Rules']].map(([id,label])=><button key={id} className={buttonClass} aria-pressed={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
 {tab==='alerts'&&<><Card className="flex flex-wrap gap-3"><select aria-label="Alert status" className={controlClass} value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{Array.from(new Set(query.data?.map(a=>a.status))).map(s=><option key={s}>{s}</option>)}</select><select aria-label="Alert severity" className={controlClass} value={severity} onChange={e=>setSeverity(e.target.value)}><option value="">All severities</option>{Array.from(new Set(query.data?.map(a=>a.severity))).map(s=><option key={s}>{s}</option>)}</select><button className={buttonClass} disabled={query.isFetching} onClick={()=>query.refetch()}>Refresh alerts</button></Card>
 {error&&<DataError error={error}/>}<DataState query={query} empty={!rows.length}><div className="grid grid-cols-1 md:grid-cols-2 gap-4">{rows.map(a=><Card key={a.id} className="space-y-3"><div className="flex justify-between"><h3 className="font-bold text-sm">{a.kind}</h3><span className="text-xs text-amber-300">{a.severity} / {a.status}</span></div><Fields value={{facility_id:a.facility_id,created_at:a.created_at,source:a.source,details:a.details}}/><div className="flex gap-2">{manage&&a.status==='open'&&<button className={buttonClass} disabled={!!busy} onClick={()=>acknowledge(a.id)}>{busy===a.id?'Acknowledging...':'Acknowledge'}</button>}{manage&&a.status!=='resolved'&&<MutationForm title="Resolve alert" path={`/alerts/${a.id}/actions`} permission="alerts.manage" fixed={{status:'resolved'}} confirm={`Resolve ${a.kind} at facility ${a.facility_id}. The alert will no longer be active.`}/>}<button className={buttonClass} onClick={()=>setSelected(a.id)}>Escalation history</button></div></Card>)}</div></DataState>
 {selected&&<DataPanel key={selected} title="Alert escalation history" path={`/alerts/${selected}/escalations`} permission="alerts.read" columns={[{key:'created_at',label:'Created at'},{key:'escalation_rule_id',label:'Rule ID'},{key:'notification_id',label:'Notification ID'}]}/>}</>}
 {tab==='rules'&&<DataPanel title="Automated Alert Triggers & Early Warning Rules" path="/alert-rules" permission="alerts.read" columns={[{key:'kind',label:'Kind'},{key:'facility_id',label:'Facility ID'},{key:'threshold',label:'Threshold'},{key:'window_days',label:'Window (days)'},{key:'severity',label:'Severity'},{key:'active',label:'Active'}]}/>}
 {tab==='notifications'&&<DataPanel title="Your notification delivery records" path="/notifications" columns={[{key:'template',label:'Template'},{key:'channel',label:'Channel'},{key:'status',label:'Status'},{key:'attempts',label:'Attempts'},{key:'failure_reason',label:'Failure reason'},{key:'delivered_at',label:'Delivered at'}]}/>}
 {tab==='escalations'&&<DataPanel title="Escalation rules" path="/escalation-rules" permission="alerts.read" columns={[{key:'rule_id',label:'Alert rule ID'},{key:'after_minutes',label:'After (minutes)'},{key:'recipient_id',label:'Recipient ID'},{key:'channel',label:'Channel'},{key:'active',label:'Active'}]}/>}
 </div>;
};
export default AlertsPage;
