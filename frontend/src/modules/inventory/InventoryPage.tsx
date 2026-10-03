import { InventoryActions } from './InventoryActions';
import { useLocation } from 'react-router-dom';
import { BatchTracePanel } from './BatchTracePanel';
import { ColdChainPanel } from './ColdChainPanel';
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';
import { PageHeading, DataState, DataPanel, DetailPanel, RecordTable, Fields, Unavailable, controlClass, buttonClass } from '@/components/common/BackendData';
import { useBackendData } from '@/hooks/useBackendData';
import { InventoryWithBatch, MedicineView, DaysOfStock, Expiry } from '@/services/backendTypes';

export const InventoryPage: React.FC = () => {
 const location = useLocation();
  const [params] = useSearchParams();
  const [facility, setFacility] = useFacilitySelection();
  const [override, setOverride] = useState(false);
  const facilityId = override ? facility : facility || params.get('facility_id') || '';
  const [tab, setTab] = useState(location.pathname.endsWith('/expiry') ? 'expiry' : 'medicines'); const [search, setSearch] = useState('');
  const [medicine, setMedicine] = useState(''); const [batch, setBatch] = useState('');
  const [barcode, setBarcode] = useState(''); const [lookup, setLookup] = useState('');
  React.useEffect(() => { setTab(location.pathname.endsWith('/expiry') ? 'expiry' : 'medicines'); setBatch(''); }, [location.pathname]);
  const catalogue = useBackendData<MedicineView[]>('/medicines', {}, 'inventory.read', true, true);
  const stock = useBackendData<InventoryWithBatch[]>('/inventory', { facility_id: facilityId }, 'inventory.read', !!facilityId, true);
  const expiry = useBackendData<Expiry[]>('/inventory/expiry', { facility_id: facilityId }, 'inventory.read', !!facilityId && tab === 'expiry', true);
  const dos = useBackendData<DaysOfStock>('/inventory/days-of-stock', { facility_id: facilityId, medicine_id: medicine }, 'inventory.read', !!facilityId && !!medicine);
  const scanned = useBackendData<object>('/barcodes/lookup', { code: lookup }, 'inventory.read', !!lookup);
  const medicineName = (id: string) => catalogue.data?.find(m => m.id === id)?.name || id;
  const rows = (stock.data || []).filter(s => `${medicineName(s.batch.medicine_id)} ${s.batch.batch_number}`.toLowerCase().includes(search.toLowerCase())).sort((a, b) => a.batch.expires_on.localeCompare(b.batch.expires_on));
  const batchRows = rows.map(s => ({ ...s, medicine_name: medicineName(s.batch.medicine_id), batch_number: s.batch.batch_number, expires_on: s.batch.expires_on, recalled: s.batch.recalled, unreserved: s.quantity - s.reserved }));
  const columns = [{ key: 'medicine_name', label: 'Medicine' }, { key: 'batch_number', label: 'Batch' }, { key: 'quantity', label: 'On hand' }, { key: 'reserved', label: 'Reserved' }, { key: 'unreserved', label: 'Unreserved (not issue eligibility)' }, { key: 'expires_on', label: 'Expires on' }, { key: 'recalled', label: 'Recalled' }];
  return <div className="space-y-6 animate-in fade-in duration-300">
    <PageHeading title="Real-Time Stock Monitoring & Batch Tracking" description="Facility stock and transaction ledger. Backend rules control FEFO allocation, recalls, reservations and safety stock." />
    <Card className="flex flex-wrap gap-3 items-center"><FacilityPicker value={facilityId} onChange={id => { setOverride(true); setFacility(id); setBatch(''); setMedicine(''); }} /><input className={controlClass} placeholder="Search by drug name or batch..." aria-label="Search inventory" value={search} onChange={e => setSearch(e.target.value)} /><button className={buttonClass} disabled={!facilityId || stock.isFetching} onClick={() => stock.refetch()}>Refresh stock</button></Card>
    <InventoryActions key={facilityId} facility={facilityId} medicines={catalogue.data || []} stock={stock.data || []}/>
    <div className="flex flex-wrap gap-2">{[['medicines','Medicine Ledger'],['batches','Batch Directory'],['lowStock','Days of Stock & Safety'],['expiry','Expiry Tracker'],['history','Stock History'],['scan','Barcode Lookup'],['recalls','Recalls'],['cold-chain','Cold Chain']].map(([id,label]) => <button key={id} className={buttonClass} aria-pressed={tab === id} onClick={() => setTab(id)}>{label}</button>)}</div>
    {(tab === 'medicines' || tab === 'batches') && <Card className="space-y-4"><h3 className="text-sm font-bold">{tab === 'batches' ? 'Granular Batch Registry' : 'Facility Medicine Ledger'}</h3><DataState query={catalogue}>{null}</DataState><DataState query={stock} empty={!rows.length}><RecordTable rows={batchRows} columns={columns} onSelect={row => { const item = rows.find(s => s.id === row.id)!; setBatch(item.batch_id); setMedicine(item.batch.medicine_id); }} /></DataState><p className="text-xs text-slate-400">Sorted by recorded expiry date for FEFO review. Expired or recalled lots remain visible for traceability; this is not a list of issuable stock.</p></Card>}
    {tab === 'lowStock' && <Card className="space-y-4"><h3 className="font-bold text-sm">Days of Stock, Safety Stock & Reorder Suggestions</h3><DataState query={catalogue} empty={!catalogue.data?.length}><select aria-label="Medicine" className={controlClass} value={medicine} onChange={e => setMedicine(e.target.value)}><option value="">Select a medicine</option>{catalogue.data?.map(m => <option key={m.id} value={m.id}>{m.name} ({m.unit})</option>)}</select></DataState><DataState query={dos}>{dos.data && <Fields value={dos.data} />}</DataState><p className="text-xs text-slate-400">No-history and zero-consumption results are not interpreted as normal stock. Null projections mean the backend cannot calculate them.</p></Card>}
    {tab === 'expiry' && <Card className="space-y-4"><h3 className="font-bold text-sm">Near-Expiry Medicine Ledger (FEFO Protocol)</h3><p className="text-xs text-slate-400">Uses the backend's configured expiry-warning window for each medicine; includes expired lots.</p><DataState query={expiry} empty={!expiry.data?.length}><RecordTable rows={(expiry.data || []).map(e => ({ ...e.inventory, medicine: medicineName(e.batch.medicine_id), batch_number: e.batch.batch_number, expires_on: e.batch.expires_on, state: e.state }))} columns={[{ key:'medicine',label:'Medicine' },{key:'batch_number',label:'Batch'},{key:'quantity',label:'Quantity'},{key:'expires_on',label:'Expires on'},{key:'state',label:'State'}]} /></DataState></Card>}
    {tab === 'history' && <DataPanel key={facilityId} title="Stock Movement Audit Trail & Chain of Custody" path="/inventory/transactions" params={{ facility_id:facilityId }} permission="inventory.read" enabled={!!facilityId} columns={[{key:'created_at',label:'Recorded at'},{key:'kind',label:'Kind'},{key:'quantity',label:'Quantity change'},{key:'reference',label:'Reference'},{key:'inventory_id',label:'Inventory ID'},{key:'actor_id',label:'Actor ID'}]} />}
    {tab === 'scan' && <Card className="space-y-4"><h3 className="font-bold text-sm">Barcode Lookup</h3><form onSubmit={e => { e.preventDefault(); setLookup(barcode.trim()); }} className="flex gap-2"><input required maxLength={128} aria-label="Barcode" className={controlClass} value={barcode} onChange={e => setBarcode(e.target.value)} /><button className={buttonClass}>Look up barcode</button></form><DataState query={scanned}>{scanned.data && <Fields value={scanned.data} />}</DataState><Unavailable>Optical camera scanning is not connected. Enter a registered barcode; unknown codes return a real not-found error.</Unavailable></Card>}
    {tab === 'cold-chain' && <ColdChainPanel facility={facilityId} />}
    {tab === 'recalls' && <DataPanel title="Recall register" path="/recalls" permission="inventory.read" columns={[{key:'batch_id',label:'Batch ID'},{key:'reason',label:'Reason'},{key:'severity',label:'Severity'},{key:'status',label:'Status'},{key:'resolution',label:'Resolution'}]} />}
    {batch && <BatchTracePanel key={`${facilityId}-${batch}`} batch={batch} />}
    <Unavailable>Predicted stockout probability, monetary wastage estimates and rack telemetry are not supplied by these APIs. Stock actions require backend confirmation. Transfer actions are in the supply-chain screen; recall administration remains read-only here.</Unavailable>
  </div>;
};
export default InventoryPage;
