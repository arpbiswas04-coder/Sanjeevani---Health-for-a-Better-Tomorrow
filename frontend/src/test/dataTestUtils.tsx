import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { vi } from 'vitest';
import { useAuthStore } from '@/store/authStore';
import { clearSession, saveTokens } from '@/services/httpClient';
import { User } from '@/types/auth';

export const facilityId = '10000000-0000-4000-8000-000000000001';
export const medicineId = '20000000-0000-4000-8000-000000000001';
export const batchId = '30000000-0000-4000-8000-000000000001';
export const fixtureFacility = { id:facilityId,name:'API Test Hospital',code:'API-TEST',facility_type:'hospital',active:true,address:'Recorded address',contact:null,block_id:null,latitude:22.5,longitude:88.3,version:1,source_device:null,created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z' };
export const fixtureBatch = {id:batchId,medicine_id:medicineId,batch_number:'API-BATCH-ONLY',expires_on:'2027-10-01',recalled:false};
export const fixtureStock = {id:'stock-1',facility_id:facilityId,batch_id:batchId,quantity:120,reserved:5,batch:fixtureBatch};
export const allPermissions = ['inventory.read','inventory.write','inventory.transfer','beds.read','workforce.read','equipment.read','reports.read','reports.export','integration.read','procurement.read','alerts.read','alerts.manage','admin.config','admin.users','audit.read'];
export function authenticate(permissions = allPermissions, scope = 'global') {
  clearSession(); saveTokens({access_token:'unit-test-access',refresh_token:'unit-test-refresh',token_type:'bearer',expires_in:900},false);
  const user: User = {id:'unit-user',name:'Test user',email:'',role:'SUPER_ADMIN',permissions:[],backendPermissions:permissions,scopeMode:scope,facilityIds:[facilityId],districtIds:[]};
  useAuthStore.setState({user,role:user.role,isAuthenticated:true,isRestoring:false,isLoading:false,error:null});
}
export const jsonResponse = (data:unknown,status=200) => new Response(JSON.stringify(status<400?{success:true,data}:{success:false,error:{message:String(data)}}),{status,headers:{'Content-Type':'application/json'}});
export function mockDataServer(overrides: Record<string,unknown> = {}) {
  const records:Record<string,unknown>={
    '/facilities':[fixtureFacility], '/medicines':[{id:medicineId,name:'API Medicine',code:'API-MED',unit:'tablet'}],
    '/inventory':[fixtureStock],'/inventory/expiry':[{inventory:fixtureStock,batch:fixtureBatch,state:'upcoming'}],
    '/inventory/days-of-stock':{current_stock:115,average_daily_consumption:null,days_of_stock:null,history_days:0,status:'no_history',safety_stock:10,transferable_stock:105,reorder_point:null,suggested_quantity:null},
    '/inventory/transactions':[{id:'tx1',kind:'receive',quantity:120,reference:'API receipt',inventory_id:'stock-1',actor_id:'actor-1',created_at:'2026-10-01T00:00:00Z'}],
    '/operations/beds':[{id:'bed-1',facility_id:facilityId,bed_type:'ICU',capacity:10,occupied:3,available:7}],
    '/operations/staff':[{id:'staff-1',display_name:'API Staff',code:'API-STAFF',staff_role_id:'role-1',active:true}],
    '/operations/attendance':[{id:'attendance-1',staff_id:'staff-1',day:'2026-10-01',status:'present'}],
    '/operations/shifts':[{id:'shift-1',staff_id:'staff-1',starts_at:'2026-10-01T00:00:00Z',ends_at:'2026-10-01T08:00:00Z',cancelled:false}],
    '/operations/footfall':[{id:'footfall-1',day:'2026-10-01',category:'API OPD',count:12}],
    '/operations/disease-counts':[{id:'disease-1',day:'2026-10-01',category:'API Disease',count:2}],
    '/operations/temperatures':[{id:'temp-1',observed_at:'2026-10-01T00:00:00Z',temperature:9,minimum:2,maximum:8,excursion:true,source:'API sensor'}],
    '/assets/equipment':[{id:'equipment-1',code:'API-VENT',equipment_type:'Ventilator',status:'available',next_maintenance:'2026-11-01'}],
    '/assets/ambulances':[{id:'ambulance-1',vehicle_id:'API-AMB',status:'available',operational:true,latitude:null,longitude:null}],
    '/alerts':[{id:'alert-1',facility_id:facilityId,kind:'LOW_STOCK',severity:'warning',status:'open',source:medicineId,details:{value:0,threshold:10},created_at:'2026-10-01T00:00:00Z'}],
    '/alert-rules':[{id:'rule-1',facility_id:facilityId,kind:'LOW_STOCK',threshold:10,window_days:90,severity:'warning',active:true}],
    '/warehouses':[{id:'warehouse-1',facility_id:facilityId,capacity:{units:100,cold_storage:true},active:true}],
    '/suppliers':[{id:'supplier-1',name:'API Supplier',code:'API-SUP',lead_days:7,active:true}],
    '/purchase-orders':[{id:'order-1',reference:'API-ORDER',supplier_id:'supplier-1',facility_id:facilityId,status:'draft'}],
    '/shipments':[{id:'shipment-1',reference:'API-SHIP',origin:'Recorded origin',facility_id:facilityId,status:'in_transit'}],
    '/transfers':[{id:'transfer-1',reference:'API-TRANSFER',source_id:facilityId,destination_id:'other-facility',status:'requested'}],
    '/barcodes/lookup':{id:'barcode-1',code:'API-CODE',medicine_id:medicineId,batch_id:batchId},
    '/reports/stock':{rows:[{...fixtureStock,medicine_name:'API Report Medicine',batch_number:'API-BATCH-ONLY'}],has_more:false,offset:0,limit:100},
    '/reports/beds':{rows:[{id:'bed-1',facility_id:facilityId,bed_type:'ICU',capacity:10,occupied:3}],has_more:false,offset:0,limit:100},
    '/users':[{id:'user-1',username:'API administrator',active:true,scope_mode:'global',mfa_required:false}],
    '/roles':[{id:'role-1',name:'API role'}],'/permissions':[{id:'permission-1',name:'inventory.read'}],
    '/audit-logs':[{id:'audit-1',action:'facility.created',details:{id:facilityId},actor_id:'user-1'}],
    ...overrides,
  };
  const request=vi.fn(async(url:RequestInfo|URL,options?:RequestInit)=>{
    const parsed=new URL(String(url));const path=parsed.pathname.replace('/api/v1','');
    if (options?.method==='POST' && path==='/alerts/alert-1/actions') {
      (records['/alerts'] as {status:string}[])[0].status='acknowledged';return jsonResponse((records['/alerts'] as object[])[0]);
    }
    if (path in records) return jsonResponse(records[path]);
    if (path.startsWith('/geography/') || ['/staff-roles','/notifications','/escalation-rules','/recalls','/cold-chain/series','/optimization/recommendations'].includes(path))return jsonResponse([]);
    if (path.endsWith('/history') || path.endsWith('/maintenance') || path.endsWith('/escalations'))return jsonResponse([]);
    return jsonResponse(`Unexpected test endpoint ${path}`,404);
  });
  vi.stubGlobal('fetch',request); return request;
}
const clients:QueryClient[]=[];
export function renderData(ui:React.ReactElement,route='/') {
  const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}});clients.push(client);
  return {...render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter></QueryClientProvider>),client};
}
export function clearDataClients(){clients.forEach(c=>c.clear());clients.length=0;}
