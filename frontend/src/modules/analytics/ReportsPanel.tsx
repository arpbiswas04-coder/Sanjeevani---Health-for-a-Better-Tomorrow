import { MutationForm } from '@/components/common/MutationForm';
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { DataError, DataState, DetailPanel, RecordTable, controlClass, buttonClass } from '@/components/common/BackendData';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { ReportResult } from '@/services/backendTypes';
import { downloadReport, downloadFile } from '@/services/dataApi';

export function ReportsPanel() {
  const [facility, setFacility] = useFacilitySelection(); const [kind, setKind] = useState('stock');
  const [medicine, setMedicine] = useState(''); const [district, setDistrict] = useState(''); const [state, setState] = useState('');
  const [status, setStatus] = useState(''); const [start, setStart] = useState(''); const [end, setEnd] = useState('');
  const [offset, setOffset] = useState(0); const [error, setError] = useState<Error | null>(null); const [busy, setBusy] = useState(false);
  const [jobInput, setJobInput] = useState(''); const [job, setJob] = useState('');
  const exporter = useCapability('reports.export'); const staff = useCapability('workforce.read');
  const params = { facility_id: facility, medicine_id: medicine, district_id: district, state_id: state, status,
    start: start ? `${start}T00:00:00Z` : undefined, end: end ? `${end}T23:59:59Z` : undefined, offset, limit: 100 };
  const query = useBackendData<ReportResult>(`/reports/${kind}`, params, 'reports.read', kind !== 'staff' || staff);
  async function download(format: 'csv' | 'pdf' | 'xlsx') {
    setError(null); setBusy(true);
    try { await downloadReport(kind, format, params); }
    catch (e) { setError(e instanceof Error ? e : new Error('Report download failed.')); }
    finally { setBusy(false); }
  }
  return <Card className="space-y-4"><h3 className="font-bold text-sm">Backend reports & downloads</h3>
    <div className="flex flex-wrap gap-3"><label className="text-xs">Report <select aria-label="Report" className={controlClass} value={kind} onChange={e => { setKind(e.target.value); setOffset(0); }}>{['stock','expiry','transfers','procurement','staff','beds','emergency'].filter(k => k !== 'staff' || staff).map(k => <option key={k}>{k}</option>)}</select></label><FacilityPicker value={facility} onChange={id => { setFacility(id); setOffset(0); }} /></div>
    <p className="text-xs text-slate-400">Without a facility filter, results cover your backend-authorized scope. Dates use UTC. Downloads contain the current page only (up to 100 rows).</p>
    <div className="flex flex-wrap gap-3">{[['Medicine ID',medicine,setMedicine],['District ID',district,setDistrict],['State ID',state,setState],['Status',status,setStatus]].map(([label,value,setter]) => <label key={String(label)} className="text-xs">{String(label)} <input aria-label={`Report ${label}`} className={controlClass} value={String(value)} onChange={e => { (setter as (s: string) => void)(e.target.value); setOffset(0); }} /></label>)}
    <label className="text-xs">From <input aria-label="Report start date" type="date" className={controlClass} value={start} onChange={e => { setStart(e.target.value); setOffset(0); }} /></label><label className="text-xs">Through <input aria-label="Report end date" type="date" className={controlClass} value={end} onChange={e => { setEnd(e.target.value); setOffset(0); }} /></label></div>
    <div className="flex gap-2"><button className={buttonClass} disabled={query.isFetching} onClick={() => query.refetch()}>Refresh report</button>{exporter && (['csv','pdf','xlsx'] as const).map(format => <button key={format} className={buttonClass} disabled={busy || !query.data || !!query.error} onClick={() => download(format)}>Download page as {format.toUpperCase()}</button>)}</div>
    {error && <DataError error={error} />}<DataState query={query} empty={!query.data?.rows.length}><RecordTable rows={query.data?.rows || []} columns={Object.keys(query.data?.rows[0] || {}).map(key => ({ key, label: key.replace(/_/g, ' ') }))} /></DataState>
    <div className="flex gap-3 items-center text-xs"><button className={buttonClass} disabled={!offset || query.isFetching} onClick={() => setOffset(Math.max(0,offset-100))}>Previous report page</button><span>Page {offset/100+1}{query.data?.has_more ? ' · More records available' : ''}</span><button className={buttonClass} disabled={!query.data?.has_more || query.isFetching} onClick={() => setOffset(offset+100)}>Next report page</button></div>
    {facility&&<MutationForm title="Request report job" path="/report-jobs" schema="ReportJobRequest" permission="reports.export" also={['reports.read',...(kind==='staff'?['workforce.read']:[])]} global={kind==='transfers'} fixed={{facility_id:facility,kind}} onSuccess={result=>{setJob(result.id);setJobInput(result.id);}} description="Create a background report for this facility and kind (up to 500 rows). Additional page filters above are not part of the job contract. Pending means queued, not completed. Retries of this request reuse its idempotency key. A new request creates a new report snapshot. There is no cancellation endpoint."/>}
    <form className="flex flex-wrap gap-2" onSubmit={e => { e.preventDefault(); setJob(jobInput.trim()); }}><input aria-label="Existing report job ID" placeholder="Existing report job ID" className={controlClass} value={jobInput} onChange={e => setJobInput(e.target.value)} required /><button className={buttonClass}>Check report job status</button></form>
    {job && <ReportJob key={job} id={job} />}
  </Card>;
}

export function ReportJob({ id }: { id: string }) {
 const query = useBackendData<{status:string;kind:string;format:string;expires_at:string}>(`/report-jobs/${id}`,{},'reports.export');
 React.useEffect(()=>{if(query.data?.status!=='pending')return;const timer=setInterval(()=>void query.refetch(),3000);return()=>clearInterval(timer);},[query.data?.status,id]);
 const [error,setError] = useState<Error|null>(null); const [busy,setBusy]=useState(false);
 return <div className="space-y-3"><DetailPanel title="Report job status" path={`/report-jobs/${id}`} permission="reports.export" />{query.data?.status==='completed' && <button className={buttonClass} disabled={busy} onClick={async()=>{setBusy(true);setError(null);try{await downloadFile(`/report-jobs/${id}/download`,`${query.data!.kind}.${query.data!.format}`);}catch(e){setError(e instanceof Error?e:new Error('Download failed.'));}finally{setBusy(false);}}}>Download completed report job</button>}{error&&<DataError error={error}/>}</div>;
}
