import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { MutationForm } from '@/components/common/MutationForm';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { SupplyActions } from '@/modules/facilities/SupplyActions';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { OperationsActions } from '@/modules/equipment/OperationsActions';
import { ReportJob } from '@/modules/analytics/ReportsPanel';
import { authenticate, clearDataClients, renderData, mockDataServer, jsonResponse, facilityId, medicineId, fixtureStock } from './dataTestUtils';
import { useAuthStore } from '@/store/authStore';
import { clearSession } from '@/services/httpClient';

beforeEach(()=>{sessionStorage.clear();authenticate(['inventory.read','inventory.write','inventory.transfer','procurement.read','procurement.write','procurement.approve','beds.read','beds.write','reports.read','reports.export']);});
afterEach(()=>{cleanup();clearDataClients();vi.unstubAllGlobals();clearSession();sessionStorage.clear();});
function open(title:string){fireEvent.click(screen.getByRole('button',{name:title}));return within(screen.getByRole('dialog'));}
function fill(label:string,value:string){fireEvent.change(screen.getByLabelText(label),{target:{value}});}

it('inventory receipt uses real form fields, Bearer request, stable idempotency and refetch rendering',async()=>{
 const stock={...fixtureStock}; const get=mockDataServer({'/inventory':[stock]}); let body:any;
 const fetcher=vi.fn(async(input:any,init?:RequestInit)=>{
  if(init?.method==='POST'){expect(new Headers(init.headers).get('Authorization')).toBe('Bearer unit-test-access');body=JSON.parse(String(init.body));stock.quantity+=body.quantity;return jsonResponse({inventory_id:stock.id,batch_id:stock.batch_id,quantity:stock.quantity},201);}
  return get(input,init);
 });vi.stubGlobal('fetch',fetcher);renderData(<InventoryPage/>,`/inventory?facility_id=${facilityId}`);
 await screen.findByText('API-BATCH-ONLY');const dialog=open('Receive stock');fill('medicine id',medicineId);fill('batch number','API-BATCH-ONLY');fill('expires on','2099-01-01');fill('quantity','5');fill('reference','receipt audit reference');fireEvent.click(dialog.getByRole('button',{name:'Save'}));
 await dialog.findByRole('status');expect(body).toMatchObject({facility_id:facilityId,medicine_id:medicineId,quantity:5,reference:'receipt audit reference'});expect(body.idempotency_key).toMatch(/^[0-9a-f-]{36}$/);expect(await screen.findByText('125')).toBeInTheDocument();
 expect(fetcher.mock.calls.filter(([,i])=>i?.method==='POST')).toHaveLength(1);
});

it('requires issue confirmation and synchronously prevents double submit while pending',async()=>{
 let finish!:(v:Response)=>void;const fetcher=vi.fn(()=>new Promise<Response>(r=>{finish=r;}));vi.stubGlobal('fetch',fetcher);
 renderData(<MutationForm title="Issue" path="/inventory/issue" schema="Issue" permission="inventory.write" fixed={{facility_id:facilityId,medicine_id:medicineId}} confirm="Deduct stock using backend FEFO."/>);
 const dialog=open('Issue');fill('quantity','2');fill('reference','issue');fireEvent.click(dialog.getByRole('button',{name:'Review change'}));expect(fetcher).not.toHaveBeenCalled();
 const confirm=dialog.getByRole('button',{name:'Confirm change'});fireEvent.click(confirm);fireEvent.click(confirm);expect(fetcher).toHaveBeenCalledTimes(1);expect(dialog.getByRole('button',{name:'Saving...'})).toBeDisabled();
 finish(jsonResponse({allocations:[]}));await dialog.findByRole('status');
});

it.each([400,401,403,404,409,422,429,500,503])('displays HTTP %i failure without confirmed success',async(status)=>{
 const fetcher=vi.fn(async()=>jsonResponse(status===409?'Insufficient usable stock':'Rejected mutation',status));vi.stubGlobal('fetch',fetcher);
 renderData(<MutationForm title="Adjust" path="/inventory/adjust" permission="inventory.write" fixed={{quantity:-2}}/>);const dialog=open('Adjust');fireEvent.click(dialog.getByRole('button',{name:'Save'}));
 if(status===401){await waitFor(()=>expect(useAuthStore.getState().user).toBeNull());expect(screen.queryByRole('dialog')).not.toBeInTheDocument();return;}
 await waitFor(()=>expect(dialog.queryByRole('status')).not.toBeInTheDocument());await waitFor(()=>expect(dialog.getAllByRole('alert').length).toBeGreaterThan(0));
 if(status===409)expect(dialog.getByText('Insufficient usable stock')).toBeInTheDocument();
});

it('retries uncertain inventory receipt with identical payload/key even after remount',async()=>{
 const bodies:any[]=[];let fail=true;vi.stubGlobal('fetch',vi.fn(async(_i,init)=>{bodies.push(JSON.parse(init.body));if(fail)throw new TypeError('offline');return jsonResponse({quantity:5});}));
 const ui=<MutationForm title="Receive" path="/inventory/receive" schema="Receive" permission="inventory.write" fixed={{facility_id:facilityId,medicine_id:medicineId,batch_number:'B',expires_on:'2099-01-01',quantity:5,reference:'R'}}/>;
 renderData(ui);let dialog=open('Receive');fireEvent.click(dialog.getByRole('button',{name:'Save'}));await dialog.findByText(/previous request may have committed/);cleanup();clearDataClients();fail=false;renderData(ui);dialog=open('Receive');fireEvent.click(dialog.getByRole('button',{name:'Retry same request'}));await dialog.findByRole('status');expect(bodies).toHaveLength(2);expect(bodies[1]).toEqual(bodies[0]);
});

it('retries a report after a lost response with the same key after remount',async()=>{
 const bodies:any[]=[];let fail=true;vi.stubGlobal('fetch',vi.fn(async(_i,init)=>{bodies.push(JSON.parse(init.body));if(fail)throw new TypeError('lost response');return jsonResponse({id:'job-1',status:'pending'},202);}));
 const ui=<MutationForm title="Request job" path="/report-jobs" schema="ReportJobRequest" permission="reports.export" fixed={{facility_id:facilityId,kind:'stock',format:'csv'}}/>;
 renderData(ui);let dialog=open('Request job');fireEvent.click(dialog.getByRole('button',{name:'Save'}));await dialog.findByText(/previous request may have committed/);cleanup();clearDataClients();fail=false;renderData(ui);dialog=open('Request job');fireEvent.click(dialog.getByRole('button',{name:'Retry same request'}));await dialog.findByRole('status');expect(bodies).toHaveLength(2);expect(bodies[1]).toEqual(bodies[0]);expect(bodies[0].idempotency_key).toMatch(/^[0-9a-f-]{36}$/);
});

it('blocks uncertain non-idempotent legacy caller resubmission rather than claiming success',async()=>{
 const fetcher=vi.fn(async()=>{throw new TypeError('offline');});vi.stubGlobal('fetch',fetcher);
 renderData(<MutationForm title="Request job" path="/report-jobs" permission="reports.export" fixed={{facility_id:facilityId,kind:'stock',format:'csv'}}/>);const dialog=open('Request job');fireEvent.click(dialog.getByRole('button',{name:'Save'}));await dialog.findByText(/previous request may have committed/);expect(dialog.getByRole('button',{name:'Retry same request'})).toBeDisabled();expect(fetcher).toHaveBeenCalledTimes(1);
});

it('read-only users have no stock mutation controls',async()=>{authenticate(['inventory.read']);mockDataServer();renderData(<InventoryPage/>,`/inventory?facility_id=${facilityId}`);await screen.findByText('API-BATCH-ONLY');expect(screen.queryByRole('button',{name:'Issue stock'})).not.toBeInTheDocument();expect(screen.queryByRole('button',{name:'Receive stock'})).not.toBeInTheDocument();});
it('expired session cannot submit a mutation',async()=>{clearSession();const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);renderData(<MutationForm title="Save" path="/beds" permission="beds.write" method="PUT"/>);expect(screen.queryByRole('button',{name:'Save'})).not.toBeInTheDocument();expect(useAuthStore.getState().user).toBeNull();expect(fetcher).not.toHaveBeenCalled();});

it('validates occupied <= capacity before any backend request',async()=>{const get=mockDataServer();renderData(<BedsPage/>);await screen.findByText('7 available');const d=open('Update bed capacity');fill('bed type','ICU');fill('capacity','2');fill('occupied','3');fireEvent.click(d.getByRole('button',{name:'Review change'}));await d.findByText('Occupancy exceeds capacity.');expect(get.mock.calls.filter(([,i])=>i?.method==='PUT')).toHaveLength(0);});

describe('backend transfer state and linked shipment gating',()=>{
 it.each([
  ['pending_approval',['approve transfer','reject transfer','cancel transfer']],
  ['approved',['dispatch transfer','cancel transfer']],
  ['dispatched',['in transit transfer','receive transfer']],
  ['in_transit',['receive transfer']],
  ['received',[]],['cancelled',[]],['rejected',[]],
 ] as [string,string[]][])('shows only valid %s actions',async(status,expected)=>{
  mockDataServer({'/transfers/t1':{id:'t1',status,reference:'REF',source_id:facilityId,destination_id:'dest',items:[]},'/transfers':[],'/shipments':[]});renderData(<SupplyActions tab="transfers" selected="t1"/>);
  await waitFor(()=>expect(screen.queryByText('Loading data...')).not.toBeInTheDocument());
  if(expected.length)await screen.findByRole('button',{name:expected[0]});
  await waitFor(()=>{const transitions=screen.queryAllByRole('button').map(b=>b.textContent).filter(x=>x?.match(/^(approve|reject|cancel|dispatch|receive|in transit) transfer$/));expect(transitions.sort()).toEqual([...expected].sort());});
 });
 it('does not offer receive until tracked shipments arrive',async()=>{mockDataServer({'/transfers/t1':{id:'t1',status:'dispatched',reference:'R'},'/shipments':[{transfer_id:'t1',status:'in_transit'}],'/transfers':[]});renderData(<SupplyActions tab="transfers" selected="t1"/>);await screen.findByRole('button',{name:'in transit transfer'});expect(screen.queryByRole('button',{name:'receive transfer'})).not.toBeInTheDocument();});
 it('does not show procurement approval without procurement.approve',async()=>{authenticate(['procurement.read','procurement.write']);mockDataServer({'/purchase-orders/p1':{id:'p1',status:'submitted',reference:'PO',items:[]},'/purchase-orders':[],'/shipments':[]});renderData(<SupplyActions tab="purchase-orders" selected="p1"/>);await screen.findByRole('button',{name:'cancel order'});expect(screen.queryByRole('button',{name:'approve order'})).not.toBeInTheDocument();});
});

it.each(['pending','failed','expired','completed'])('report job %s is represented without fabricated completion',async(status)=>{mockDataServer({'/report-jobs/r1':{id:'r1',status,kind:'stock',format:'csv',failure_code:status==='failed'?'ACCESS_REVOKED':null}});renderData(<ReportJob id="r1"/>);await screen.findByText(status);expect(!!screen.queryByRole('button',{name:'Download completed report job'})).toBe(status==='completed');});
it('narrow beds writer does not acquire inventory permission or request directories',()=>{authenticate(['beds.read','beds.write'],'restricted');const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);renderData(<OperationsActions kind="beds" facility={facilityId}/>);expect(screen.getByRole('button',{name:'Update bed capacity'})).toBeInTheDocument();expect(fetcher).not.toHaveBeenCalled();});

it('changing supply tabs keeps one action section and exactly two transfer facility selectors',async()=>{
 authenticate(['inventory.read','inventory.transfer','facility.manage','procurement.read','procurement.write']);mockDataServer();renderData(<WarehouseDashboardPage/>);
 await screen.findByRole('button',{name:'Register warehouse'});
 fireEvent.click(screen.getByRole('button',{name:'Stock transfers',exact:true}));
 await waitFor(()=>expect(screen.getAllByRole('region',{name:'Supply chain actions'})).toHaveLength(1));
 expect(screen.getAllByLabelText('Facility')).toHaveLength(2);
 fireEvent.click(screen.getByRole('button',{name:'Suppliers',exact:true}));expect(screen.queryByLabelText('Facility')).not.toBeInTheDocument();
});
