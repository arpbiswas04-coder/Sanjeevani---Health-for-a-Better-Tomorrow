import { useHealth } from '@/hooks/useHealth';
import { Card } from '@/components/ui/Card';
import { DataState, Fields } from '@/components/common/BackendData';
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { PageHeading, DataPanel, DetailPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
export const AdminPage: React.FC = () => {
 const location=useLocation(); const pathTab=location.pathname.split('/').pop();
 const [tab,setTab]=useState(['users','roles','audit-logs','monitoring'].includes(pathTab||'')?pathTab!:'users');
 useEffect(()=>{setTab(['users','roles','audit-logs','monitoring'].includes(pathTab||'')?pathTab!:'users');},[pathTab]);
 return <div className="space-y-6"><PageHeading title="System Administration & Platform Governance" description="Backend user, permission, configuration and audit records. User provisioning and permission assignment remain intentionally read-only in this operational integration; use the governed administration APIs."/>
 <div className="flex gap-2 flex-wrap">{['users','roles','audit-logs','monitoring'].map(t=><button key={t} className={buttonClass} aria-pressed={tab===t} onClick={()=>setTab(t)}>{t}</button>)}</div>
 {tab==='users'&&<DataPanel title="Registered users" path="/users" permission="admin.users" columns={[{key:'username',label:'Username'},{key:'active',label:'Active'},{key:'scope_mode',label:'Scope mode'},{key:'mfa_required',label:'MFA required'},{key:'created_at',label:'Created at'}]}/>}
 {tab==='roles'&&<><DataPanel title="Backend roles" path="/roles" permission="admin.users" paginated={false} columns={[{key:'id',label:'ID'},{key:'name',label:'Name'}]}/><DataPanel title="Backend permission catalogue" path="/permissions" permission="admin.users" paginated={false} columns={[{key:'id',label:'ID'},{key:'name',label:'Name'}]}/></>}
 {tab==='audit-logs'&&<DataPanel title="Audit logs" path="/audit-logs" permission="audit.read" columns={[{key:'created_at',label:'Recorded at'},{key:'actor_id',label:'Actor ID'},{key:'action',label:'Action'},{key:'details',label:'Details'}]}/>}
 {tab==='monitoring'&&<><BackendHealth /><DetailPanel title="Public backend configuration" path="/admin/config" permission="admin.config"/><DetailPanel title="Backup architecture status" path="/admin/backups/status" permission="admin.config"/><Unavailable>Connection-pool utilization, cache hit rates and federated compute node health have no monitoring endpoint. Backup status is reported metadata, not proof of a restore test.</Unavailable></>}
 </div>;
};
export default AdminPage;

function BackendHealth() {
 const query = useHealth();
 return <Card className="space-y-3"><h3 className="text-sm font-bold">Backend API liveness</h3><DataState query={query}>{query.data && <Fields value={query.data} />}</DataState><p className="text-xs text-slate-400">This endpoint proves API liveness only; it does not verify database or Redis readiness.</p></Card>;
}
