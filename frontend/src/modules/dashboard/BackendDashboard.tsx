import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataState, DataPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { FacilityView, AlertView, ReportResult, BedCapacityView } from '@/services/backendTypes';
import { getData } from '@/services/dataApi';
import { useAuthStore } from '@/store/authStore';
import { ReportsPanel } from '@/modules/analytics/ReportsPanel';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

function CountCard({ title, path, permission, facility }: { title: string; path: string; permission: string; facility?: string }) {
  const query = useBackendData<object[]>(path, facility === undefined ? {} : { facility_id: facility }, permission, facility === undefined || !!facility, true);
  return <Card className="space-y-3"><h3 className="text-xs text-slate-400">{title}</h3><DataState query={query}><p className="text-2xl font-bold font-mono">{query.data?.length}</p></DataState></Card>;
}
export function BackendDashboard({ title }: { title: string }) {
  const [facility, setFacility] = useFacilitySelection(); const user = useAuthStore(s => s.user);
  const reports = useCapability('reports.read');
  const facilities = useBackendData<FacilityView[]>('/facilities', { active: true }, 'inventory.read', true, true);
  const alerts = useBackendData<AlertView[]>('/alerts', {}, 'alerts.read', true, true);
  const beds = useQuery({ queryKey: ['backend', user?.id, user?.scopeMode, user?.facilityIds, user?.districtIds, user?.backendPermissions, 'dashboard-beds', facility], enabled: reports, retry: false,
    queryFn: async () => {
      const rows: BedCapacityView[] = [];
      for (let offset=0; offset<20000; offset+=500) {
        const page = await getData<ReportResult>('/reports/beds', { facility_id: facility, offset, limit: 500 });
        rows.push(...page.rows as BedCapacityView[]); if (!page.has_more) return rows;
      }
      throw new Error('Too many bed records. Select a facility to narrow the dashboard.');
    },
  });
  const capacity = beds.data?.reduce((sum,b) => sum+b.capacity,0) || 0;
  const occupied = beds.data?.reduce((sum,b) => sum+b.occupied,0) || 0;
  return <div className="space-y-6 animate-in fade-in duration-200"><PageHeading title={title} description="Backend records for your permitted scope. Counts are fetched through all pages; facility selection applies to operational cards and the bed chart." />
    <Card><FacilityPicker value={facility} onChange={setFacility} /></Card>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="space-y-3"><h3 className="text-xs text-slate-400">Active facilities in scope</h3><DataState query={facilities}><p className="text-2xl font-bold">{facilities.data?.length}</p></DataState></Card>
      <Card className="space-y-3"><h3 className="text-xs text-slate-400">Recorded Bed Occupancy</h3>{reports ? <DataState query={beds} empty={!beds.data?.length}><p className="text-2xl font-bold">{capacity ? `${(100*occupied/capacity).toFixed(1)}%` : 'Not calculable'}</p><p className="text-xs">{occupied} occupied / {capacity} capacity</p></DataState> : <Unavailable>Requires reports.read.</Unavailable>}</Card>
      <Card className="space-y-3"><h3 className="text-xs text-slate-400">Unresolved alerts in scope</h3><DataState query={alerts}><p className="text-2xl font-bold">{alerts.data?.filter(a => a.status !== 'resolved').length}</p></DataState></Card>
      <CountCard title="Purchase orders in scope" path="/purchase-orders" permission="procurement.read" />
      <CountCard title="Inventory batch records — selected facility" path="/inventory" permission="inventory.read" facility={facility} />
      <CountCard title="Equipment records — selected facility" path="/assets/equipment" permission="equipment.read" facility={facility} />
      <CountCard title="Ambulance records — selected facility" path="/assets/ambulances" permission="equipment.read" facility={facility} />
      <CountCard title="Staff records — selected facility" path="/operations/staff" permission="workforce.read" facility={facility} />
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5"><Card className="space-y-4"><div className="flex justify-between"><h3 className="font-bold text-sm">Recorded bed capacity and occupancy</h3><button className={buttonClass} disabled={!reports || beds.isFetching} onClick={() => beds.refetch()}>Refresh beds chart</button></div>{reports ? <DataState query={beds} empty={!beds.data?.length}><div className="h-60"><ResponsiveContainer width="100%" height="100%"><BarChart data={beds.isError ? [] : beds.data}><CartesianGrid stroke="#1e293b" /><XAxis dataKey="bed_type" /><YAxis /><Tooltip /><Bar dataKey="capacity" fill="#38bdf8" /><Bar dataKey="occupied" fill="#a855f7" /></BarChart></ResponsiveContainer></div></DataState> : <Unavailable>Requires reports.read.</Unavailable>}</Card>
    <Card className="space-y-4"><h3 className="font-bold text-sm">Medicine runway, resilience & predicted demand</h3><Unavailable>No national medicine-availability score, resilience benchmark, forecast or oxygen-runway endpoint exists. Facility-specific days of stock are available in Inventory.</Unavailable></Card></div>
    <DataPanel key={facility} title="Patient footfall — selected facility" path="/operations/footfall" params={{ facility_id: facility }} permission="integration.read" enabled={!!facility} columns={[{key:'day',label:'Day'},{key:'category',label:'Category'},{key:'count',label:'Count'}]} />
    <ReportsPanel />
  </div>;
}
