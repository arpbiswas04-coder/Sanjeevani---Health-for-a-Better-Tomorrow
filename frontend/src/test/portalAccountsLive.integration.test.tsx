import React from 'react';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { LoginPage } from '@/modules/auth/LoginPage';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { RoleGuard } from '@/components/common/RoleGuard';
import { NAVIGATION_BY_ROLE } from '@/app/navigationConfig';
import { canAccessPath } from '@/app/authorization';
import { Role } from '@/types/auth';
import { useAuthStore } from '@/store/authStore';
import { clearSession, readSession } from '@/services/httpClient';

const enabled=process.env.PORTAL_ACCOUNTS_LIVE==='1';
const profiles=['admin','national','state','district','facility','operator','inventory','reader'];
const clients:QueryClient[]=[];
function mount(ui:React.ReactElement,route='/login'){
 const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}});clients.push(client);
 return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter></QueryClientProvider>);
}
function CurrentRoute(){return <span data-testid="route">{useLocation().pathname}</span>;}
afterEach(async()=>{cleanup();for(const client of clients){await client.cancelQueries();client.clear();}clients.length=0;if(readSession())await useAuthStore.getState().logout();clearSession();});

it.skipIf(!enabled).each(profiles)('real %s portal selection, navigation, data and denial',async(profile)=>{
 const read=(file:string)=>JSON.parse(readFileSync(path.resolve('..',file),'utf8'));
 const credentials={...read('tmp/development-data/credentials.json'),...read('tmp/development-data/portal-credentials.json')};
 const facts=read('tmp/portal-accounts/http.json');const expected=facts.accounts[profile];const cred=credentials[profile];
 const portal:Role=profile==='admin'?'SUPER_ADMIN':profile==='national'?'NATIONAL_ADMIN':profile==='state'?'STATE_ADMIN':profile==='district'?'DISTRICT_ADMIN':'FACILITY_ADMIN';
 const landing=profile==='admin'?'/admin/dashboard':`/${['national','state','district'].includes(profile)?profile:'facility'}/dashboard`;
 useAuthStore.setState({isRestoring:false,isLoading:false,error:null});
 mount(<><LoginPage/><CurrentRoute/></>);
 fireEvent.change(screen.getByLabelText('Official Email / Username'),{target:{value:cred.username}});
 fireEvent.change(screen.getByLabelText('Passcode / Password'),{target:{value:cred.password}});
 fireEvent.change(screen.getByLabelText('Role'),{target:{value:portal}});
 fireEvent.click(screen.getByRole('button',{name:'Sign In to Command Portal'}));
 await waitFor(()=>expect(screen.getByTestId('route')).toHaveTextContent(landing),{timeout:10000});
 const user=useAuthStore.getState().user!;
 expect(user.role).toBe(portal);expect(user.backendRoles).toEqual([expected.role]);
 expect(user.backendPermissions!.slice().sort()).toEqual(expected.permissions.slice().sort());
 expect(user.districtIds!.slice().sort()).toEqual(expected.district_ids.slice().sort());
 expect(user.facilityIds!.slice().sort()).toEqual(expected.facility_ids.slice().sort());
 cleanup();mount(<RoleSidebar/>,landing);
 for(const section of NAVIGATION_BY_ROLE[portal])for(const item of section.items){
  // Badges are part of a link's accessible name; assert the destination and label.
  const link=screen.queryAllByRole('link').find(element=>element.getAttribute('href')===item.path);
  if(canAccessPath(item.path,user)){expect(link).toHaveAttribute('href',item.path);expect(link).toHaveTextContent(item.name);}else expect(link).toBeUndefined();
 }
 cleanup();mount(<RoleGuard><FacilitiesPage/></RoleGuard>,'/facilities');
 expect(await screen.findByRole('heading',{name:expected.selected_facility_name})).toBeInTheDocument();
 if(profile!=='admin'){
  cleanup();mount(<Routes><Route path="/admin/users" element={<RoleGuard allowedRoles={['SUPER_ADMIN']}><div>Forbidden user administration</div></RoleGuard>}/><Route path="/unauthorized" element={<div>Access correctly denied</div>}/></Routes>,'/admin/users');
  expect(await screen.findByText('Access correctly denied')).toBeInTheDocument();
  expect(screen.queryByText('Forbidden user administration')).toBeNull();
 }
 const token=readSession()!.accessToken;await useAuthStore.getState().logout();
 expect((await fetch(`${facts.api}/api/v1/users/me`,{headers:{Authorization:`Bearer ${token}`}})).status).toBe(401);
 cleanup();mount(<LoginPage/>);
 fireEvent.change(screen.getByLabelText('Official Email / Username'),{target:{value:cred.username}});
 fireEvent.change(screen.getByLabelText('Passcode / Password'),{target:{value:cred.password}});
 fireEvent.change(screen.getByLabelText('Role'),{target:{value:portal==='NATIONAL_ADMIN'?'FACILITY_ADMIN':'NATIONAL_ADMIN'}});
 fireEvent.click(screen.getByRole('button',{name:'Sign In to Command Portal'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('not assigned to this portal role');
 expect(readSession()).toBeNull();expect(useAuthStore.getState().isAuthenticated).toBe(false);
},60000);
