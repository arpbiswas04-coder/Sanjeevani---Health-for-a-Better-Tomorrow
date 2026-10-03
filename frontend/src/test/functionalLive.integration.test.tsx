import React from 'react';
import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation, Routes, Route } from 'react-router-dom';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { LoginPage } from '@/modules/auth/LoginPage';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { BackendDashboard } from '@/modules/dashboard/BackendDashboard';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { RoleGuard } from '@/components/common/RoleGuard';
import { useAuthStore } from '@/store/authStore';
import { clearSession, readSession, apiRequest } from '@/services/httpClient';

// Real React forms/client/HTTP/PostgreSQL. Shared setup mocks only Leaflet's DOM
// renderer; these checks do not claim browser tile rendering or visual acceptance.
const enabled=process.env.FUNCTIONAL_LIVE_TEST==='1';
const privateFile=process.env.FUNCTIONAL_LIVE_CREDENTIALS_FILE || path.resolve('../tmp/development-data/credentials.json');
const factsFile=process.env.FUNCTIONAL_LIVE_FACTS_FILE || path.resolve('../tmp/functional-completion/http-verification.json');
const clients:QueryClient[]=[];
function mount(ui:React.ReactElement,initialPath='/'){
 const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}});clients.push(client);
 return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[initialPath]}>{ui}</MemoryRouter></QueryClientProvider>);
}
function RouteEcho(){return <span data-testid="current-route">{useLocation().pathname}</span>;}
afterEach(async()=>{cleanup();for(const client of clients){await client.cancelQueries();client.clear();}clients.length=0;if(readSession())await useAuthStore.getState().logout();clearSession();});

it.skipIf(!enabled).each(['admin','operator','inventory','reader'])('real %s login, navigation and populated React pages',async(profile)=>{
 const accounts=JSON.parse(readFileSync(privateFile,'utf8'));const facts=JSON.parse(readFileSync(factsFile,'utf8'));
 expect(facts.api).toMatch(/^http:\/\/(127\.0\.0\.1|localhost):/);expect(facts.arpan_unchanged).toBe(true);
 const expected=facts.profiles[profile];const cred=accounts[profile];
 useAuthStore.setState({isRestoring:false,isLoading:false,error:null});
 mount(<><LoginPage/><RouteEcho/></>);
 fireEvent.change(screen.getByLabelText('Official Email / Username'),{target:{value:cred.username}});
 fireEvent.change(screen.getByLabelText('Passcode / Password'),{target:{value:cred.password}});
 fireEvent.click(screen.getByRole('button',{name:'Sign In to Command Portal'}));
 await waitFor(()=>expect(useAuthStore.getState().isAuthenticated).toBe(true),{timeout:10000});
 expect(readSession()!.accessToken.split('.')).toHaveLength(3);
 expect(useAuthStore.getState().user!.backendRoles).toEqual([expected.role]);
 expect(useAuthStore.getState().user!.backendPermissions!.slice().sort()).toEqual(expected.permissions);
 expect(useAuthStore.getState().user!.facilityIds!.slice().sort()).toEqual(expected.facility_ids);
 expect(screen.getByTestId('current-route')).toHaveTextContent(profile==='admin'?'/admin/dashboard':'/facility/dashboard');
 cleanup();mount(<RoleSidebar/>);
 expect(screen.getByRole('link',{name:'Supply Chain'})).toHaveAttribute('href','/warehouses');
 expect(screen.getByRole('link',{name:'Resource Map'})).toHaveAttribute('href','/map');
 if(profile==='inventory')expect(screen.queryByRole('link',{name:'Staff Rosters'})).toBeNull();
 if(profile!=='admin')expect(screen.queryByRole('link',{name:'Users & Personnel'})).toBeNull();
 cleanup();mount(<BackendDashboard title="Live development dashboard"/>);
 const dashboardFacility=screen.getAllByLabelText('Facility')[0];
 await within(dashboardFacility).findByRole('option',{name:new RegExp(facts.selected_facility.name)});
 fireEvent.change(dashboardFacility,{target:{value:facts.selected_facility.id}});
 await waitFor(()=>expect(within(screen.getByText('Inventory batch records — selected facility').parentElement!).getByText(String(expected.inventory_records))).toBeInTheDocument(),{timeout:10000});
 expect(await screen.findByText('18 occupied / 20 capacity')).toBeInTheDocument();
 cleanup();mount(<FacilitiesPage/>);
 expect(await screen.findByRole('heading',{name:facts.selected_facility.name})).toBeInTheDocument();
 cleanup();mount(<RoleGuard><InventoryPage/></RoleGuard>,'/inventory');
 await screen.findByRole('option',{name:new RegExp(facts.selected_facility.name)});
 fireEvent.change(screen.getByLabelText('Facility'),{target:{value:facts.selected_facility.id}});
 expect(await screen.findByText('DEVOPS-20261003-ENRICH-LOT')).toBeInTheDocument();
 if(profile==='reader')expect(screen.queryByText('Receive stock')).toBeNull();
 cleanup();mount(<AlertsPage/>);expect((await screen.findAllByText('LOW_STOCK')).length).toBeGreaterThan(0);
 if(profile==='reader')expect(screen.queryByRole('button',{name:'Acknowledge'})).toBeNull();
 if(expected.permissions.includes('workforce.read')){
  cleanup();mount(<WorkforcePage/>);await screen.findByRole('option',{name:new RegExp(facts.selected_facility.name)});
  fireEvent.change(screen.getByLabelText('Facility'),{target:{value:facts.selected_facility.id}});
  expect(await screen.findByText(facts.staff_code)).toBeInTheDocument();
 }else await expect(apiRequest(`/api/v1/operations/staff?facility_id=${facts.selected_facility.id}`)).rejects.toMatchObject({status:403});
 cleanup();mount(<WarehouseDashboardPage/>);fireEvent.click(screen.getByRole('button',{name:'Procurement'}));
 expect(await screen.findByText('DEVOPS-20261003-ENRICH-PO')).toBeInTheDocument();
 if(expected.permissions.includes('integration.read')){
  cleanup();mount(<AIDashboard/>);fireEvent.click(screen.getByRole('button',{name:'Historical Trend & Utilization'}));
  await screen.findByRole('option',{name:new RegExp(facts.selected_facility.name)});
  fireEvent.change(screen.getByLabelText('Facility'),{target:{value:facts.selected_facility.id}});
  fireEvent.change(screen.getByLabelText('Consumption medicine ID'),{target:{value:facts.consumption.medicine_id}});
  fireEvent.change(screen.getByLabelText('Consumption start date'),{target:{value:facts.consumption.day}});
  fireEvent.change(screen.getByLabelText('Consumption end date'),{target:{value:facts.consumption.day}});
  const day=await screen.findByText(facts.consumption.day);
  expect(within(day.closest('tr')!).getByText(String(facts.consumption.consumed))).toBeInTheDocument();
 }
 cleanup();mount(<InteractiveResourceMap/>);
 expect(await screen.findByText(new RegExp(`Nodes visible: ${expected.map_count} /`))).toBeInTheDocument();
 expect((await screen.findAllByText(/Approximate city reference:/)).length).toBeGreaterThan(0);
 cleanup();
 if(profile==='admin'){
  // Match router.tsx: system administrators may inspect regional presentations.
  mount(<RoleGuard allowedRoles={['NATIONAL_ADMIN','SUPER_ADMIN']}><div>Verified regional access</div></RoleGuard>,'/national/dashboard');
  expect(screen.getByText('Verified regional access')).toBeInTheDocument();
 }else{
  mount(<Routes><Route path="/admin/users" element={<RoleGuard allowedRoles={['SUPER_ADMIN']}><div>Forbidden content</div></RoleGuard>}/><Route path="/unauthorized" element={<div>Verified role denial</div>}/></Routes>,'/admin/users');
  expect(await screen.findByText('Verified role denial')).toBeInTheDocument();
  expect(screen.queryByText('Forbidden content')).toBeNull();
 }
 const token=readSession()!.accessToken;await useAuthStore.getState().logout();
 expect(readSession()).toBeNull();
 const response=await fetch(`${facts.api}/api/v1/users/me`,{headers:{Authorization:`Bearer ${token}`}});expect(response.status).toBe(401);
 cleanup();mount(<LoginPage/>);
 fireEvent.change(screen.getByLabelText('Official Email / Username'),{target:{value:cred.username}});
 fireEvent.change(screen.getByLabelText('Passcode / Password'),{target:{value:cred.password}});
 fireEvent.change(screen.getByLabelText('Role'),{target:{value:profile==='admin'?'FACILITY_ADMIN':'SUPER_ADMIN'}});
 fireEvent.click(screen.getByRole('button',{name:'Sign In to Command Portal'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('not assigned to this portal role');
 expect(readSession()).toBeNull();expect(useAuthStore.getState().isAuthenticated).toBe(false);
},60000);
