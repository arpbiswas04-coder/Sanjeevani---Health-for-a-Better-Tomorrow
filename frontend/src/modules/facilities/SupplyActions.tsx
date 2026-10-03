import { useState } from 'react';
import { MutationForm, Options, Values } from '@/components/common/MutationForm';
import { useBackendData, useCapability } from '@/hooks/useBackendData';
import { DataState, buttonClass, controlClass } from '@/components/common/BackendData';
import { FacilityPicker, useFacilitySelection } from '@/components/common/FacilityPicker';

const transferTransitions:Record<string,string[]>={pending_approval:['approve','reject','cancel'],approved:['dispatch','cancel'],dispatched:['in_transit','receive'],in_transit:['receive']};
const orderTransitions:Record<string,string[]>={draft:['submit','cancel'],submitted:['approve','cancel'],approved:['order','cancel'],ordered:['cancel']};
const shipmentTransitions:Record<string,string[]>={planned:['dispatched','cancelled'],dispatched:['in_transit','arrived'],in_transit:['arrived']};
export { transferTransitions, orderTransitions, shipmentTransitions };
export function SupplyActions({tab, selected}:{tab:string;selected:string}) {
 const [facility,setFacility]=useFacilitySelection(); const [destination,setDestination]=useState('');
 const manage=useCapability(tab==='transfers'?'inventory.transfer':tab==='warehouses'?'facility.manage':'procurement.write');
 const inventory=useCapability('inventory.read'); const procurement=useCapability('procurement.read');
 const medicine=useBackendData<Values[]>('/medicines',{},'inventory.read',manage&&inventory,true);
 const stock=useBackendData<Values[]>('/inventory',{facility_id:facility},'inventory.read',manage&&inventory&&tab==='transfers'&&!!facility,true);
 const suppliers=useBackendData<Values[]>('/suppliers',{},'procurement.read',manage&&procurement&&tab==='purchase-orders',true);
 const list=useBackendData<Values[]>(`/${tab}`,{},tab==='transfers'||tab==='warehouses'?'inventory.read':'procurement.read',manage&&!!selected,true);
 const detail=useBackendData<Values>(`/${tab}/${selected}`,{},tab==='transfers'?'inventory.read':'procurement.read',manage&&!!selected&&['transfers','purchase-orders'].includes(tab));
 const shipments=useBackendData<Values[]>('/shipments',{},'procurement.read',manage&&procurement&&['transfers','purchase-orders'].includes(tab),true);
 const sourceOrders=useBackendData<Values[]>('/purchase-orders',{},'procurement.read',manage&&tab==='shipments',true);
 const sourceTransfers=useBackendData<Values[]>('/transfers',{},'inventory.read',manage&&inventory&&tab==='shipments',true);
 const [source,setSource]=useState('order');
 const row=['transfers','purchase-orders'].includes(tab)?detail.data:list.data?.find(r=>r.id===selected);
 const parentId=row?.order_id||row?.transfer_id;
 const parent=useBackendData<Values>(`${row?.order_id?'/purchase-orders':'/transfers'}/${parentId}`,{},row?.order_id?'procurement.read':'inventory.read',tab==='shipments'&&!!parentId&&manage);
 if(!manage)return null;
 const options:Options={medicine_id:(medicine.data||[]).map(r=>({value:r.id,label:r.name})),batch_id:(stock.data||[]).map(r=>({value:r.batch_id,label:r.batch.batch_number})),supplier_id:(suppliers.data||[]).filter(r=>r.active).map(r=>({value:r.id,label:r.name}))};
 const linked=(shipments.data||[]).filter(s=>tab==='transfers'?s.transfer_id===selected:s.order_id===selected);
 // Missing shipment-read permission means lifecycle eligibility cannot be established safely.
 const movementKnown=procurement && !!shipments.data && !shipments.error;
 const noActiveShipment=movementKnown&&!linked.some(s=>s.status!=='cancelled');
 const arrived=movementKnown&&!linked.some(s=>!['arrived','cancelled'].includes(s.status));
 return <section aria-label="Supply chain actions" className="space-y-3">
 {['transfers','purchase-orders','warehouses'].includes(tab)&&<FacilityPicker value={facility} onChange={setFacility}/>}
 <div className="flex flex-wrap gap-2">
 {tab==='suppliers'&&<MutationForm title="Create supplier" path="/suppliers" schema="SupplierInput" permission="procurement.write" global/>}
 {tab==='suppliers'&&row&&<MutationForm key={selected} title="Edit supplier" path={`/suppliers/${selected}`} method="PUT" schema="SupplierInput" permission="procurement.write" global defaults={row} confirm="Save supplier details and active status. Inactive suppliers cannot receive new purchase orders."/>}
 {tab==='warehouses'&&facility&&<MutationForm title="Register warehouse" path="/warehouses" schema="WarehouseInput" permission="facility.manage" fixed={{facility_id:facility}} confirm="Register this facility as a warehouse. Its facility type will change to warehouse."/>}
 {tab==='warehouses'&&row&&<MutationForm key={selected} title="Edit warehouse" path={`/warehouses/${selected}`} method="PUT" schema="WarehouseUpdate" permission="facility.manage" defaults={{capacity_units:row.capacity.units,cold_storage:row.capacity.cold_storage,active:row.active}} confirm="Save warehouse capacity and active state. Active state also changes its parent facility."/>}
 {tab==='purchase-orders'&&facility&&medicine.data&&suppliers.data&&<MutationForm title="Create purchase order" path="/purchase-orders" schema="OrderInput" permission="procurement.write" fixed={{facility_id:facility}} options={options} validate={b=>new Set(b.items.map((i:Values)=>i.medicine_id)).size!==b.items.length?'Medicine lines must be unique.':undefined} description="Use a unique procurement reference. The backend rejects duplicate references; it does not accept an idempotency key for order creation."/>}
 </div>
 {tab==='transfers'&&<><label className="text-xs">Destination facility</label><FacilityPicker value={destination} onChange={setDestination}/>{facility&&destination&&stock.data&&<MutationForm title="Create transfer" path="/transfers" schema="TransferCreate" permission="inventory.transfer" fixed={{source_id:facility,destination_id:destination}} options={options} validate={b=>b.source_id===b.destination_id?'Source and destination must differ.':new Set(b.items.map((i:Values)=>i.batch_id)).size!==b.items.length?'Batch lines must be unique.':undefined}/>}</>}
 {selected&&<DataState query={['transfers','purchase-orders'].includes(tab)?detail:list}>{null}</DataState>}
 {row&&['transfers','purchase-orders'].includes(tab)&&<div className="flex flex-wrap gap-2">{(tab==='transfers'?transferTransitions:orderTransitions)[row.status]?.filter(action=>action==='cancel'?noActiveShipment:action==='receive'?arrived:true).map(action=><MutationForm key={`${row.id}-${row.status}-${action}`} title={`${action.replace(/_/g,' ')} ${tab==='transfers'?'transfer':'order'}`} path={`/${tab}/${selected}/actions`} schema={tab==='transfers'?'TransferAction':'OrderAction'} permission={tab==='transfers'?'inventory.transfer':'procurement.write'} also={tab==='purchase-orders'&&action==='approve'?['procurement.approve']:[]} fixed={{action}} confirm={['dispatch','receive','cancel','reject'].includes(action)?`${action} ${row.reference} (${row.id}). Source/destination: ${row.source_id||row.facility_id} ${row.destination_id||''}. Transfer dispatch deducts stock; receipt credits stock; cancellation releases reservations. See selected record items and history below.`:undefined}/>)}</div>}
 {row&&tab==='purchase-orders'&&['ordered','partially_received'].includes(row.status)&&arrived&&<MutationForm title="Receive purchase order" path={`/purchase-orders/${selected}/receive`} schema="OrderReceipt" permission="procurement.write" also={['inventory.write']} options={{item_id:row.items.filter((i:Values)=>i.received<i.quantity).map((i:Values)=>({value:i.id,label:`${i.medicine_id}: ${i.quantity-i.received} remaining`}))}} confirm={`Receive stock against order ${row.reference} into facility ${row.facility_id}.`} validate={b=>b.quantity>row.items.find((i:Values)=>i.id===b.item_id)?.quantity-row.items.find((i:Values)=>i.id===b.item_id)?.received?'Receipt exceeds remaining order quantity.':undefined}/>}
 {tab==='shipments'&&<><label className="text-xs">Shipment source <select aria-label="Shipment source" className={controlClass} value={source} onChange={e=>setSource(e.target.value)}><option value="order">Purchase order</option><option value="transfer">Transfer</option></select></label><MutationForm key={source} title="Create shipment" path="/shipments" schema="ShipmentInput" permission="procurement.write" fixed={source==='order'?{transfer_id:null}:{order_id:null}} options={{[source==='order'?'order_id':'transfer_id']:(source==='order'?sourceOrders.data||[]:sourceTransfers.data||[]).filter(r=>(source==='order'?['ordered','partially_received']:['approved','dispatched','in_transit']).includes(r.status)).map(r=>({value:r.id,label:r.reference}))}} validate={b=>!b.order_id&&!b.transfer_id?'Select an eligible order or transfer.':undefined}/></>}
 {tab==='shipments'&&row&&<div className="flex gap-2">{shipmentTransitions[row.status]?.filter(status=>status==='cancelled'||(parent.data&&(row.order_id?['ordered','partially_received']:['dispatched','in_transit','received']).includes(parent.data.status))).map(status=><MutationForm key={`${row.id}-${row.status}-${status}`} title={`Mark shipment ${status}`} path={`/shipments/${selected}/actions`} schema="ShipmentAction" permission="procurement.write" fixed={{status}} confirm={`Change shipment ${row.reference} to ${status}. Arrival does not receive inventory; use the order or transfer receipt action.`}/>)}</div>}
 {row&&['transfers','purchase-orders'].includes(tab)&&!movementKnown&&<p className="text-xs">Cancel/receive eligibility requires procurement.read and a successful shipment lookup. No additional permission is granted here.</p>}
 </section>;
}
