import { AdminPage } from '@/modules/admin/AdminPage';
import { BatchTracePanel } from '@/modules/inventory/BatchTracePanel';
import { ColdChainPanel } from '@/modules/inventory/ColdChainPanel';
import { RegisterPage } from '@/modules/auth/RegisterPage';
import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { authenticate, mockDataServer, renderData, clearDataClients, fixtureFacility, facilityId, medicineId, fixtureStock, jsonResponse } from './dataTestUtils';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { EquipmentPage } from '@/modules/equipment/EquipmentPage';
import { PatientsPage } from '@/modules/patients/PatientsPage';
import { DiseasePage } from '@/modules/disease/DiseasePage';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { NationalDashboardPage } from '@/modules/dashboard/NationalDashboardPage';
import { FederatedAIPage } from '@/modules/federated-ai/FederatedAIPage';
import { EmergencyPage } from '@/modules/emergency/EmergencyPage';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { ReportsPanel } from '@/modules/analytics/ReportsPanel';
import { OfflineIndicator } from '@/components/common/OfflineIndicator';
import { offlineStorage } from '@/utils/offlineStorage';
import { DataPanel } from '@/components/common/BackendData';
import { clearSession, apiRequest } from '@/services/httpClient';
import { apiPath, getDirectory, downloadReport } from '@/services/dataApi';
import { useAuthStore } from '@/store/authStore';
import { canAccessPath } from '@/app/authorization';

beforeEach(()=>{authenticate();mockDataServer();});
afterEach(()=>{cleanup();clearDataClients();clearSession();vi.unstubAllGlobals();vi.restoreAllMocks();});

it('renders backend facility metadata and filters actual records without invented telemetry',async()=>{
 const fetch=mockDataServer();renderData(<FacilitiesPage/>);
 expect(await screen.findByText('API Test Hospital')).toBeInTheDocument();
 expect(screen.getByText('Recorded address')).toBeInTheDocument();expect(screen.queryByText('Medicine Stock')).toBeNull();
 expect(fetch.mock.calls.every(([,options])=>new Headers(options?.headers).get('Authorization')==='Bearer unit-test-access')).toBe(true);
 fireEvent.change(screen.getByLabelText('Search facilities'),{target:{value:'no-match'}});
 expect(screen.getByText(/No records in your permitted scope/)).toBeInTheDocument();
});
it('renders only backend map coordinates and disables unsupported heatmaps',async()=>{
 mockDataServer({'/facilities':[fixtureFacility,{...fixtureFacility,id:'missing',name:'No coordinates',latitude:null,longitude:null}]});renderData(<InteractiveResourceMap/>);
 await screen.findByText(/Nodes visible: 1/);expect(screen.getAllByTestId('circle-marker')).toHaveLength(1);
 expect(screen.getByText(/1 facilities without coordinates/)).toBeInTheDocument();expect(screen.getByRole('button',{name:/Disease Heatmap/})).toBeDisabled();
});
it('renders inventory and batches from the selected facility without fake dispensing or transfer actions',async()=>{
 const fetch=mockDataServer();renderData(<InventoryPage/>);await screen.findByText('API Medicine');
 expect(screen.getByText('API-BATCH-ONLY')).toBeInTheDocument();expect(screen.getByText('115')).toBeInTheDocument();
 expect(fetch.mock.calls.some(([url])=>String(url).includes(`/inventory?facility_id=${facilityId}`))).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Batch Directory'}));expect(screen.getByText('API-BATCH-ONLY')).toBeInTheDocument();
 expect(screen.queryByRole('button',{name:/Dispense|Authorize & Dispatch/})).toBeNull();
 expect(screen.getByRole('button',{name:'Receive stock'})).toBeInTheDocument();
 expect(fetch.mock.calls.filter(([,options])=>options?.method==='POST')).toHaveLength(0);
});
it('uses configured expiry windows without sending a hardcoded days override',async()=>{
 const fetch=mockDataServer();renderData(<InventoryPage/>);fireEvent.click(screen.getByRole('button',{name:'Expiry Tracker'}));await screen.findByText('upcoming');
 const call=fetch.mock.calls.find(([url])=>String(url).includes('/inventory/expiry'))!;expect(new URL(String(call[0])).searchParams.has('days')).toBe(false);
 expect(screen.queryByText(/Monetary Wastage Risk Value/)).toBeNull();
});
it('shows no-history and null projections honestly while rendering safety stock',async()=>{
 renderData(<InventoryPage/>);fireEvent.click(screen.getByRole('button',{name:'Days of Stock & Safety'}));await screen.findByRole('option',{name:'API Medicine (tablet)'});
 fireEvent.change(screen.getByLabelText('Medicine'),{target:{value:medicineId}});await screen.findByText('no_history');expect(screen.getByText('10')).toBeInTheDocument();expect(screen.getAllByText('Not recorded').length).toBeGreaterThan(0);
});
it('looks up a real barcode and never substitutes the first inventory record for unknown input',async()=>{
 const fetch=mockDataServer();renderData(<InventoryPage/>);fireEvent.click(screen.getByRole('button',{name:'Barcode Lookup'}));fireEvent.change(screen.getByLabelText('Barcode'),{target:{value:'API-CODE'}});fireEvent.click(screen.getByRole('button',{name:'Look up barcode'}));await screen.findByText('barcode-1');
 expect(fetch.mock.calls.some(([url])=>String(url).includes('code=API-CODE'))).toBe(true);
 fetch.mockResolvedValue(jsonResponse('Unknown barcode',404));fireEvent.change(screen.getByLabelText('Barcode'),{target:{value:'unknown'}});fireEvent.click(screen.getByRole('button',{name:'Look up barcode'}));expect(await screen.findByRole('alert')).toHaveTextContent('Unknown barcode');expect(screen.queryByText('barcode-1')).toBeNull();
});
it.each([[BedsPage,'7 available','/operations/beds'],[WorkforcePage,'API Staff','/operations/staff'],[EquipmentPage,'API-VENT','/assets/equipment'],[PatientsPage,'API OPD','/operations/footfall'],[DiseasePage,'API Disease','/operations/disease-counts']] as const)('renders scoped records in %s',async(Component,label,path)=>{
 const fetch=mockDataServer();renderData(<Component/>);await screen.findByText(label);expect(fetch.mock.calls.some(([url])=>String(url).includes(`${path}?facility_id=${facilityId}`))).toBe(true);
});
it('reads shifts and attendance without claiming biometrics or paging success',async()=>{
 renderData(<WorkforcePage/>);fireEvent.click(screen.getByRole('button',{name:'Shift Roster'}));await screen.findByText('2026-10-01T08:00:00Z');fireEvent.click(screen.getByRole('button',{name:'Attendance',exact:true}));await screen.findByText('present');expect(screen.queryByText('RFID + Iris Verified')).toBeNull();
});
it('reads ambulance statuses exactly and exposes no simulated dispatch action',async()=>{
 renderData(<EquipmentPage/>);fireEvent.click(screen.getByRole('button',{name:'Ambulance Fleet'}));await screen.findByText('API-AMB');expect(screen.getByText('available')).toBeInTheDocument();expect(screen.queryByRole('button',{name:/Dispatch/})).toBeNull();
});
it.each([['Suppliers','API Supplier','/suppliers'],['Procurement','API-ORDER','/purchase-orders'],['Shipments','API-SHIP','/shipments'],['Stock transfers','API-TRANSFER','/transfers']])('reads %s without fabricated status transitions',async(tab,label,path)=>{
 const fetch=mockDataServer();renderData(<WarehouseDashboardPage/>);fireEvent.click(screen.getByRole('button',{name:tab,exact:true}));await screen.findByText(label);expect(fetch.mock.calls.some(([url])=>new URL(String(url)).pathname===`/api/v1${path}`)).toBe(true);expect(fetch.mock.calls.every(([,options])=>!options?.method||options.method==='GET')).toBe(true);
});
it('acknowledges an incident through the API then re-fetches server status',async()=>{
 const fetch=mockDataServer();renderData(<AlertsPage/>);await screen.findByText('LOW_STOCK');fireEvent.click(screen.getByRole('button',{name:'Acknowledge'}));await waitFor(()=>expect(screen.queryByRole('button',{name:'Acknowledge'})).toBeNull());
 const call=fetch.mock.calls.find(([,options])=>options?.method==='POST')!;expect(String(call[0])).toMatch(/\/alerts\/alert-1\/actions$/);expect(JSON.parse(String(call[1]?.body))).toEqual({status:'acknowledged'});expect(screen.getByText(/warning \/ acknowledged/)).toBeInTheDocument();
});
it('shows backend threshold rules, not hardcoded stock/ICU trigger claims',async()=>{
 renderData(<AlertsPage/>);fireEvent.click(screen.getByRole('button',{name:'Threshold Engine'}));await screen.findByText('LOW_STOCK');expect(screen.getByText('10')).toBeInTheDocument();
});
it('hides acknowledgement without alerts.manage even for a frontend administrator role',async()=>{
 authenticate(['alerts.read']);const fetch=mockDataServer();renderData(<AlertsPage/>);await screen.findByText('LOW_STOCK');expect(screen.queryByRole('button',{name:'Acknowledge'})).toBeNull();expect(fetch.mock.calls.every(([,options])=>options?.method!=='POST')).toBe(true);
});
it('supports a beds-only assigned user without fetching facilities or granting inventory.read',async()=>{
 authenticate(['beds.read'],'restricted');const fetch=mockDataServer();renderData(<BedsPage/>);await screen.findByText('7 available');expect(screen.getByLabelText('Facility ID')).toHaveValue(facilityId);expect(fetch.mock.calls.every(([url])=>!String(url).includes('/facilities'))).toBe(true);expect(useAuthStore.getState().user?.backendPermissions).toEqual(['beds.read']);expect(canAccessPath('/facilities',useAuthStore.getState().user)).toBe(false);
});
it('keeps successful dashboard cards usable when another request fails',async()=>{
 const normal=mockDataServer();const impl=normal.getMockImplementation()!;normal.mockImplementation(async(...args)=>String(args[0]).includes('/alerts')?jsonResponse('outage',503):impl(...args));renderData(<NationalDashboardPage/>);await screen.findByText('30.0%');expect(await screen.findByRole('alert')).toHaveAttribute('data-state','BACKEND_UNAVAILABLE');expect(screen.queryByText('1,428')).toBeNull();
});
it('does not show stale successful records after a failed refetch',async()=>{
 const fetch=mockDataServer();renderData(<FacilitiesPage/>);await screen.findByText('API Test Hospital');fetch.mockRejectedValue(new TypeError('network down'));fireEvent.click(screen.getByRole('button',{name:'Refresh facilities'}));await screen.findByRole('alert');expect(screen.queryByText('API Test Hospital')).toBeNull();
});
it.each([[403,'FORBIDDEN'],[404,'NOT_FOUND'],[409,'CONFLICT'],[422,'VALIDATION_ERROR'],[503,'BACKEND_UNAVAILABLE']])('distinguishes backend HTTP %s failures',async(status,state)=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(jsonResponse('contract failure',status)));renderData(<DataPanel title="Probe" path="/alerts" permission="alerts.read" columns={[{key:'kind',label:'Kind'}]}/>);expect(await screen.findByRole('alert')).toHaveAttribute('data-state',state);expect(screen.queryByText('LOW_STOCK')).toBeNull();
});
it('distinguishes network failures from successful empty data',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('offline')));renderData(<DataPanel title="Probe" path="/alerts" permission="alerts.read" columns={[]}/>);expect(await screen.findByRole('alert')).toHaveAttribute('data-state','NETWORK_ERROR');
});
it('shows loading before the response and empty only after successful completion',async()=>{
 let resolve!:(value:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(r=>resolve=r)));renderData(<DataPanel title="Probe" path="/alerts" permission="alerts.read" columns={[]}/>);expect(screen.getByRole('status')).toHaveAttribute('data-state','LOADING');await act(async()=>resolve(jsonResponse([])));expect(await screen.findByRole('status')).toHaveAttribute('data-state','SUCCESS_EMPTY');
});
it('shows unauthorized without issuing requests when no user is signed in',async()=>{
 clearSession();const fetch=vi.fn();vi.stubGlobal('fetch',fetch);renderData(<DataPanel title="Probe" path="/alerts" permission="alerts.read" columns={[]}/>);expect(screen.getByRole('alert')).toHaveAttribute('data-state','UNAUTHORIZED');expect(fetch).not.toHaveBeenCalled();
});
it('clears the session if the API and refresh both reject authorization',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue(jsonResponse('revoked',401)));await expect(apiRequest('/api/v1/alerts')).rejects.toMatchObject({status:401});expect(useAuthStore.getState().isAuthenticated).toBe(false);
});
it('isolates cached records when the authenticated identity or scope changes',async()=>{
 const fetch=mockDataServer();renderData(<FacilitiesPage/>);await screen.findByText('API Test Hospital');fetch.mockResolvedValue(jsonResponse([]));act(()=>useAuthStore.setState({user:{...useAuthStore.getState().user!,id:'different-user',facilityIds:[]}}));await waitFor(()=>expect(screen.queryByText('API Test Hospital')).toBeNull());await screen.findByText(/No records in your permitted scope/);
});
it('serializes false and zero query values and fetches all list pages',async()=>{
 expect(apiPath('/facilities',{active:false,offset:0,search:'a & b',unset:undefined})).toBe('/api/v1/facilities?active=false&offset=0&search=a+%26+b');
 const fetch=vi.fn().mockResolvedValueOnce(jsonResponse(Array.from({length:200},(_,id)=>({id})))).mockResolvedValueOnce(jsonResponse([{id:200}]));vi.stubGlobal('fetch',fetch);expect(await getDirectory('/facilities')).toHaveLength(201);expect(String(fetch.mock.calls[1][0])).toContain('offset=200');
});
it('renders real report results and clearly labels page-limited downloads',async()=>{
 renderData(<ReportsPanel/>);await screen.findByText('API Report Medicine');expect(screen.getByText(/current page only/)).toBeInTheDocument();expect(screen.getByRole('button',{name:'Next report page'})).toBeDisabled();expect(screen.getByRole('button',{name:'Download page as PDF'})).toBeEnabled();
});
it.each(['csv','pdf','xlsx'] as const)('downloads %s through the authenticated client',async(format)=>{
 const create=vi.fn(()=> 'blob:unit-test');Object.defineProperty(URL,'createObjectURL',{configurable:true,value:create});Object.defineProperty(URL,'revokeObjectURL',{configurable:true,value:vi.fn()});vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 const fetch=vi.fn().mockResolvedValue(new Response('actual bytes',{status:200}));vi.stubGlobal('fetch',fetch);await downloadReport('stock',format,{facility_id:facilityId,offset:0,limit:100});expect(create).toHaveBeenCalledOnce();expect(fetch.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer unit-test-access');expect(String(fetch.mock.calls[0][0])).toContain(`format=${format}`);
});
it('does not expose exports to a read-only report user',async()=>{
 authenticate(['reports.read']);renderData(<ReportsPanel/>);await screen.findByText('API Report Medicine');expect(screen.queryByRole('button',{name:/Download page/})).toBeNull();
});
it('federated and emergency screens expose unsupported states without fabricated operational claims',()=>{
 renderData(<FederatedAIPage/>);expect(screen.getAllByText(/No working backend source/)).toHaveLength(4);expect(screen.queryByText(/AIIMS New Delhi Trauma Edge Node/)).toBeNull();cleanup();renderData(<EmergencyPage/>);expect(screen.queryByText('DEFCON-1 Active')).toBeNull();expect(screen.queryByRole('button',{name:/ACTIVATE CRISIS|Compute Resilience/})).toBeNull();expect(screen.getByText(/What-if simulations/)).toBeInTheDocument();
});
it.each(['Demand Forecasting','Cost & Wastage Reduction','Resilience & Risk Scores','District Comparison & Benchmarking'])('labels unsupported %s honestly',tab=>{
 renderData(<AIDashboard/>);fireEvent.click(screen.getByRole('button',{name:tab}));expect(screen.getByText(/no working endpoint/)).toBeInTheDocument();expect(screen.queryByText(/42.8 Lakhs/)).toBeNull();
});
it('never deletes an offline queue while pretending to synchronize it',()=>{
 offlineStorage.enqueue({endpoint:'/unconnected',method:'POST',payload:{test:true}});renderData(<OfflineIndicator/>);expect(screen.getByRole('button',{name:'Sync unavailable'})).toBeDisabled();fireEvent.click(screen.getByRole('button',{name:'Sync unavailable'}));expect(offlineStorage.getQueue()).toHaveLength(1);offlineStorage.clearQueue();
});

it('pages both trace sections without presenting the first page as complete',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce(jsonResponse({batch:{batch_number:'TRACE-LOT'},inventory:[],transactions:Array.from({length:50},(_,id)=>({id,kind:'receive',quantity:1,reference:`receipt-${id}`}))})).mockResolvedValueOnce(jsonResponse({batch:{batch_number:'TRACE-LOT'},inventory:[],transactions:[]}));vi.stubGlobal('fetch',fetch);renderData(<BatchTracePanel batch="batch-1"/>);await screen.findByText('receipt-49');fireEvent.click(screen.getByRole('button',{name:'Next trace page'}));await waitFor(()=>expect(screen.getByRole('button',{name:'Next trace page'})).toBeDisabled());expect(String(fetch.mock.calls[1][0])).toContain('offset=50');
});
it('reads cold-chain observations and submits UTC bounds for the time series',async()=>{
 const fetch=mockDataServer();renderData(<ColdChainPanel facility={facilityId}/>);await screen.findByText('API sensor');fireEvent.change(screen.getByLabelText('Cold-chain start'),{target:{value:'2026-10-01T00:00'}});fireEvent.change(screen.getByLabelText('Cold-chain end'),{target:{value:'2026-10-02T00:00'}});await waitFor(()=>expect(fetch.mock.calls.some(([url])=>new URL(String(url)).pathname==='/api/v1/cold-chain/series')).toBe(true));const url=new URL(String(fetch.mock.calls.find(([url])=>new URL(String(url)).pathname==='/api/v1/cold-chain/series')![0]));expect(url.searchParams.get('start')).toBe('2026-10-01T00:00:00Z');expect(url.searchParams.get('facility_id')).toBe(facilityId);
});
it('does not collect credentials for unsupported self-registration',()=>{
 const fetch=mockDataServer();renderData(<RegisterPage/>);expect(screen.getByRole('status')).toHaveTextContent('Self-registration is unavailable');expect(screen.queryByRole('button',{name:'Submit Registration'})).toBeNull();expect(document.querySelector('input[type=password]')).toBeNull();expect(fetch).not.toHaveBeenCalled();
});
it.each([[InventoryPage,'/facility/expiry','Near-Expiry Medicine Ledger (FEFO Protocol)'],[WorkforcePage,'/facility/attendance','Attendance Records'],[EquipmentPage,'/facility/ambulance','Ambulance register']] as const)('opens the operational tab specified by route %s', (Component,route,title)=>{
 renderData(<Component/>,route);expect(screen.getByRole('heading',{name:title})).toBeInTheDocument();
});

it('shows real admin records and describes liveness without claiming dependency health',async()=>{
 const fetch=mockDataServer({'/admin/config':{auth_rate_limit:20},'/admin/backups/status':{healthy:false,verification_reported:false}});const impl=fetch.getMockImplementation()!;fetch.mockImplementation(async(...args)=>String(args[0]).endsWith('/health')?new Response(JSON.stringify({status:'ok',service:'FastAPI test liveness'}),{status:200}):impl(...args));renderData(<AdminPage/>,'/admin/monitoring');await screen.findByText('FastAPI test liveness');expect(screen.getByText(/does not verify database or Redis readiness/)).toBeInTheDocument();await screen.findByText('auth rate limit');
});
