import React from 'react';
import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { LoginPage } from '@/modules/auth/LoginPage';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { ReportsPanel } from '@/modules/analytics/ReportsPanel';
import { useAuthStore } from '@/store/authStore';
import { clearSession, readSession, apiRequest } from '@/services/httpClient';
import { getData } from '@/services/dataApi';

const enabled=process.env.MUTATIONS_LIVE_TEST==='1';
const fixture=JSON.parse(process.env.MUTATIONS_LIVE_FIXTURE||'{}');
const clients:QueryClient[]=[];
function view(ui:React.ReactElement,route='/') {const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}});clients.push(client);render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter></QueryClientProvider>);}
function probe(action:string,id:string) {const backend=path.resolve('../backend');return execFileSync(path.join(backend,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),['scripts/verify_phase4_data.py',action,id],{cwd:backend,encoding:'utf8'});}
function stored(kind:string) {return JSON.parse(probe('inspect',fixture.facilities[kind].id));}
function fill(label:string,value:string) {fireEvent.change(screen.getByLabelText(label),{target:{value}});}
async function login() {
 expect(fixture.database).toBe('sanjeevani_dev');expect(fixture.run).toMatch(/^DEV-P4-/);
 useAuthStore.setState({isRestoring:false,isLoading:false,error:null});view(<LoginPage/>);
 fill('Official Email / Username',process.env.AUTH_LIVE_USERNAME!);fill('Passcode / Password',process.env.AUTH_LIVE_PASSWORD!);
 fireEvent.click(screen.getByRole('button',{name:'Sign In to Command Portal'}));await waitFor(()=>expect(useAuthStore.getState().isAuthenticated).toBe(true),{timeout:10000});expect(readSession()!.accessToken.split('.')).toHaveLength(3);cleanup();
}
async function save(title:string,fields:Record<string,string>,confirmed=false) {
 fireEvent.click(screen.getByRole('button',{name:title,exact:true}));const d=within(screen.getByRole('dialog'));
 for(const [name,value] of Object.entries(fields))fill(name,value);
 const submit=d.getByRole('button',{name:confirmed?'Review change':'Save'});fireEvent.click(submit);
 if(confirmed){const confirm=d.getByRole('button',{name:'Confirm change'});fireEvent.click(confirm);fireEvent.click(confirm);}
 await d.findByRole('status',{}, {timeout:10000});await waitFor(()=>expect(d.getByRole('button',{name:'Close completed action'})).toBeEnabled());fireEvent.click(d.getByRole('button',{name:'Close completed action'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
}
async function selectFacility(kind:string) {await waitFor(()=>expect(screen.getAllByRole('option').some(o=>o.getAttribute('value')===fixture.facilities[kind].id)).toBe(true));fill('Facility',fixture.facilities[kind].id);}
afterEach(()=>{cleanup();clients.forEach(c=>c.clear());clients.length=0;clearSession();});

it.skipIf(!enabled)('LIVE inventory receipt/issue/adjust -> PostgreSQL ledger -> refetched React, and rejection leaves DB unchanged',async()=>{
 await login();const before=stored('inventory');view(<InventoryPage/>,`/inventory?facility_id=${fixture.facilities.inventory.id}`);
 await screen.findByText(fixture.run,{}, {timeout:10000});
 const batches=await getData<{batch_id:string;batch:{expires_on:string}}[]>('/inventory',{facility_id:fixture.facilities.inventory.id});
 const expires=batches.find(b=>b.batch_id===fixture.batch_id)!.batch.expires_on;
 await save('Receive stock',{'medicine id':fixture.medicine_id,'batch number':fixture.run,'expires on':expires,'quantity':'10','reference':fixture.run+' receipt'});
 expect(stored('inventory').quantity).toBe(before.quantity+10);expect((await screen.findAllByText(String(before.quantity+10))).length).toBeGreaterThan(0);
 await save('Issue stock',{'medicine id':fixture.medicine_id,'quantity':'4','reference':fixture.run+' issue'},true);
 expect(stored('inventory').quantity).toBe(before.quantity+6);expect((await screen.findAllByText(String(before.quantity+6))).length).toBeGreaterThan(0);
 await save('Adjust stock',{'batch id':fixture.batch_id,'quantity':'1','reference':fixture.run+' counted adjustment'},true);
 const accepted=stored('inventory');expect(accepted.quantity).toBe(before.quantity+7);expect(accepted.ledger_count).toBe(before.ledger_count+3);expect((await screen.findAllByText(String(accepted.quantity))).length).toBeGreaterThan(0);
 fireEvent.click(screen.getByRole('button',{name:'Issue stock'}));fill('medicine id',fixture.medicine_id);fill('quantity',String(accepted.quantity+100));fill('reference','Rejected development-only issue');fireEvent.click(screen.getByRole('button',{name:'Review change'}));fireEvent.click(screen.getByRole('button',{name:'Confirm change'}));await screen.findByText('Insufficient usable stock',{}, {timeout:10000});
 expect(stored('inventory')).toEqual(accepted);
},90000);

it.skipIf(!enabled)('LIVE complete transfer lifecycle -> source/destination PostgreSQL quantities -> refreshed React states',async()=>{
 await login();const source=stored('transfer').quantity,destination=stored('destination').quantity;view(<WarehouseDashboardPage/>);
 fireEvent.click(screen.getByRole('button',{name:'Stock transfers',exact:true}));
 await waitFor(()=>expect(screen.getAllByRole('option').some(o=>o.getAttribute('value')===fixture.facilities.transfer.id)).toBe(true));
 fireEvent.change(screen.getAllByLabelText('Facility')[0],{target:{value:fixture.facilities.transfer.id}});fireEvent.change(screen.getAllByLabelText('Facility')[1],{target:{value:fixture.facilities.destination.id}});
 const reference=fixture.run+'-transfer-'+Date.now();await screen.findByRole('button',{name:'Create transfer'});
 await save('Create transfer',{'reference':reference,'items 1 batch id':fixture.batch_id,'items 1 quantity':'5'});
 const row=await screen.findByText(reference);fireEvent.click(within(row.closest('tr')!).getByRole('button',{name:'View details'}));
 for(const action of ['approve','dispatch','in transit','receive']) {
  await screen.findByRole('button',{name:action+' transfer'}, {timeout:10000});await save(action+' transfer',{'reason':fixture.run+' '+action},['dispatch','receive'].includes(action));
 }
 expect(stored('transfer').quantity).toBe(source-5);expect(stored('destination').quantity).toBe(destination+5);expect(stored('transfer').transfers.some((t:any)=>t.status==='received')).toBe(true);
 await waitFor(()=>expect(screen.getAllByText('received').length).toBeGreaterThan(0));expect(screen.queryByRole('button',{name:'receive transfer'})).not.toBeInTheDocument();
 const stock=await getData<any[]>('/inventory',{facility_id:fixture.facilities.destination.id});expect(stock[0].quantity).toBe(destination+5);
},90000);

it.skipIf(!enabled)('LIVE alert acknowledge and resolution -> PostgreSQL -> refetched incident UI',async()=>{
 await login();probe('alert',fixture.facilities.alerts.id);const alert=stored('alerts').alerts.find((a:any)=>a.status==='open');expect(alert).toBeTruthy();view(<AlertsPage/>);
 const ids=await screen.findAllByText(fixture.facilities.alerts.id,{}, {timeout:10000});const card=ids.map(id=>id.closest('dl')!.parentElement!).find(c=>within(c).queryByText('warning / open'))!;expect(card).toBeTruthy();
 fireEvent.click(within(card).getByRole('button',{name:'Acknowledge'}));await waitFor(()=>expect(within(card).getByText('warning / acknowledged')).toBeInTheDocument());expect(stored('alerts').alerts.find((a:any)=>a.id===alert.id).status).toBe('acknowledged');
 fireEvent.click(within(card).getByRole('button',{name:'Resolve alert'}));fireEvent.click(screen.getByRole('button',{name:'Review change'}));fireEvent.click(screen.getByRole('button',{name:'Confirm change'}));await screen.findByText(/Backend confirmed resolve alert/);expect(stored('alerts').alerts.find((a:any)=>a.id===alert.id).status).toBe('resolved');await waitFor(()=>expect(within(card).getByText('warning / resolved')).toBeInTheDocument());
},60000);

it.skipIf(!enabled)('LIVE bed mutation from React -> PostgreSQL -> updated available count, then restore through UI',async()=>{
 await login();const before=stored('operations').beds[0];view(<BedsPage/>);await selectFacility('operations');await screen.findByText(`${before.capacity-before.occupied} available`);
 try {await save('Update bed capacity',{'bed type':fixture.run,'capacity':String(before.capacity),'occupied':'4'},true);expect(stored('operations').beds[0].occupied).toBe(4);await screen.findByText(`${before.capacity-4} available`);}
 finally {await save('Update bed capacity',{'bed type':fixture.run,'capacity':String(before.capacity),'occupied':String(before.occupied)},true);expect(stored('operations').beds[0].occupied).toBe(before.occupied);}
},90000);

it.skipIf(!enabled)('LIVE report request -> PostgreSQL pending -> scoped real generator -> polling -> completed React and bytes',async()=>{
 await login();const before=stored('reports').jobs.map((j:any)=>j.id);view(<ReportsPanel/>);await selectFacility('reports');await save('Request report job',{});
 const created=stored('reports').jobs.filter((j:any)=>!before.includes(j.id));expect(created).toHaveLength(1);const job=created[0];expect(job.status).toBe('pending');await screen.findByText('pending');expect(screen.queryByRole('button',{name:'Download completed report job'})).not.toBeInTheDocument();
 probe('generate',job.id);expect(stored('reports').jobs.find((j:any)=>j.id===job.id).status).toBe('completed');await screen.findByRole('button',{name:'Download completed report job'},{timeout:10000});const blob=await apiRequest<Blob>(`/api/v1/report-jobs/${job.id}/download`,{},'blob');expect(await blob.text()).toContain(fixture.medicine_name);
},90000);
