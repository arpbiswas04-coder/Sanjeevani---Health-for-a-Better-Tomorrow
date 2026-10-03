import React from 'react';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { FacilityView } from '@/services/backendTypes';
import { useAuthStore } from '@/store/authStore';
import { controlClass, DataState } from './BackendData';

export function FacilityPicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const user = useAuthStore(state => state.user);
  const directoryAllowed = useCapability('inventory.read');
  const query = useBackendData<FacilityView[]>('/facilities', { active: true }, 'inventory.read', directoryAllowed, true);
  if (!directoryAllowed) return <div className="space-y-2 text-xs text-slate-400">
    <label>Facility ID <input aria-label="Facility ID" className={controlClass} value={value} onChange={e => onChange(e.target.value)} list="assigned-facilities" /></label>
    <datalist id="assigned-facilities">{user?.facilityIds?.map(id => <option key={id} value={id} />)}</datalist>
    <p>Facility names require inventory access. Use an assigned facility ID; the backend verifies your scope.</p>
  </div>;
  return <div className="space-y-2"><label className="text-xs text-slate-400">Facility <select aria-label="Facility" className={`${controlClass} ml-2`} value={value} onChange={e => onChange(e.target.value)}>
    <option value="">Select a facility</option>{query.data?.map(f => <option key={f.id} value={f.id}>{f.name} ({f.code})</option>)}
  </select></label><DataState query={query} empty={query.data?.length === 0}><span className="text-xs text-slate-500">Active facilities in your permitted scope</span></DataState></div>;
}
export function useFacilitySelection() {
  const user = useAuthStore(state => state.user);
  const [selection, setSelection] = React.useState({ owner: user?.id, id: user?.facilityIds?.length === 1 ? user.facilityIds[0] : '' });
  const id = selection.owner === user?.id ? selection.id : '';
  return [id, (next: string) => setSelection({ owner: user?.id, id: next })] as const;
}
