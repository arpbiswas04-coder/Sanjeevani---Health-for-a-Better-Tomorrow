import { SupplyActions } from './SupplyActions';
import React, { useState } from 'react';
import { PageHeading, DataPanel, DetailPanel, Unavailable, buttonClass } from '@/components/common/BackendData';
import { useCapability } from '@/hooks/useBackendData';
export const WarehouseDashboardPage: React.FC = () => {
 const [tab,setTab]=useState('warehouses'); const [selected,setSelected]=useState(''); const globalMetrics=useCapability('procurement.read',true);
 const definitions:Record<string,{title:string;permission:string;columns:{key:string;label:string}[]}>= {
 warehouses:{title:'Strategic Warehouses',permission:'inventory.read',columns:[{key:'id',label:'Warehouse ID'},{key:'facility_id',label:'Facility ID'},{key:'capacity',label:'Recorded capacity'},{key:'active',label:'Active'}]},
 suppliers:{title:'Suppliers',permission:'procurement.read',columns:[{key:'name',label:'Name'},{key:'code',label:'Code'},{key:'contact',label:'Contact'},{key:'lead_days',label:'Lead days'},{key:'active',label:'Active'}]},
 'purchase-orders':{title:'Procurement',permission:'procurement.read',columns:[{key:'reference',label:'Reference'},{key:'supplier_id',label:'Supplier ID'},{key:'facility_id',label:'Facility ID'},{key:'status',label:'Status'}]},
 shipments:{title:'Live Logistics & Redistribution Dispatch Queue',permission:'procurement.read',columns:[{key:'reference',label:'Reference'},{key:'origin',label:'Origin'},{key:'facility_id',label:'Destination facility ID'},{key:'status',label:'Status'},{key:'expected_at',label:'Expected at'},{key:'arrived_at',label:'Arrived at'}]},
 transfers:{title:'Stock transfers',permission:'inventory.read',columns:[{key:'reference',label:'Reference'},{key:'source_id',label:'Source facility ID'},{key:'destination_id',label:'Destination facility ID'},{key:'status',label:'Status'}]}};
 const current=definitions[tab];
 return <div className="space-y-6"><PageHeading title="Warehouse Network & Cold-Chain Capacity Dashboard" description="Supply chain records and authorized operational actions. Backend rules control every transition."/>
 <div className="flex flex-wrap gap-2">{Object.entries(definitions).map(([id,d])=><button key={id} className={buttonClass} aria-pressed={tab===id} onClick={()=>{setTab(id);setSelected('');}}>{id==='shipments'?'Shipments':d.title}</button>)}</div>
 <SupplyActions key={`actions-${tab}`} tab={tab} selected={selected}/>
 <DataPanel key={tab} title={current.title} path={`/${tab}`} permission={current.permission} columns={current.columns} onSelect={row=>setSelected(String(row.id))}/>
 {selected&&tab==='warehouses'&&<DataPanel key={selected} title="Warehouse stock" path={`/warehouses/${selected}/inventory`} permission="inventory.read" columns={[{key:'batch_id',label:'Batch ID'},{key:'quantity',label:'Quantity'},{key:'reserved',label:'Reserved'}]}/>}
 {selected&&tab==='suppliers'&&(globalMetrics?<DetailPanel key={selected} title="Supplier performance metrics" path={`/suppliers/${selected}/metrics`} permission="procurement.read"/>:<Unavailable>Supplier metrics require global scope.</Unavailable>)}
 {selected&&(tab==='purchase-orders'||tab==='transfers')&&<DetailPanel key={selected} title={tab==='transfers'?'Transfer items and history':'Purchase order items'} path={`/${tab}/${selected}`} permission={current.permission}/>}
 {selected&&tab==='shipments'&&<DataPanel key={selected} title="Shipment history" path={`/shipments/${selected}/history`} permission="procurement.read" paginated={false} columns={[{key:'created_at',label:'Recorded at'},{key:'status',label:'Status'},{key:'note',label:'Note'},{key:'actor_id',label:'Actor ID'}]}/>}
 <Unavailable>Capacity utilization percentages, driver identities and optimized ETAs are not supplied. Capacity metadata is displayed exactly as stored.</Unavailable></div>;
};
export default WarehouseDashboardPage;
