import React from 'react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, screen, fireEvent } from '@testing-library/react';
import { Link } from 'react-router-dom';
import { authenticate, mockDataServer, renderData, clearDataClients, fixtureFacility } from './dataTestUtils';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { EquipmentPage } from '@/modules/equipment/EquipmentPage';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { useAuthStore } from '@/store/authStore';
import { clearSession } from '@/services/httpClient';

beforeEach(()=>{authenticate();mockDataServer();});
afterEach(()=>{cleanup();clearDataClients();clearSession();vi.unstubAllGlobals();});

it('labels and groups approximate city references without replacing exact coordinates',async()=>{
 const location_context={precision:'approximate_city',city:'Anand',state:'Gujarat',latitude:22.55251,longitude:72.9552,reference_id:'1278685',attribution:'GeoNames, CC BY 4.0'};
 mockDataServer({'/facilities':[fixtureFacility,
  {...fixtureFacility,id:'approx-1',name:'Source One',latitude:null,longitude:null,location_context},
  {...fixtureFacility,id:'approx-2',name:'Source Two',latitude:null,longitude:null,location_context},
  {...fixtureFacility,id:'missing',name:'No location',latitude:null,longitude:null}],
  '/geography/states':[{id:'gujarat',name:'Gujarat'}]});
 renderData(<InteractiveResourceMap/>);
 expect(await screen.findByText(/Nodes visible: 3/)).toHaveTextContent('1 facilities without coordinates');
 expect(screen.getAllByTestId('circle-marker')).toHaveLength(2);
 expect(screen.getAllByText(/Approximate city reference: Anand/)).toHaveLength(2);
 fireEvent.change(screen.getByLabelText('State'),{target:{value:'gujarat'}});
 expect(screen.getByText(/Nodes visible: 2/)).toBeInTheDocument();
 expect(screen.getAllByTestId('circle-marker')).toHaveLength(1);
 fireEvent.change(screen.getByLabelText('Search map facilities'),{target:{value:'missing search'}});
 expect(screen.getByText(/No records in your permitted scope/)).toBeInTheDocument();
});

it.each([
 {Page:InventoryPage,destination:'/facility/expiry',initial:'Facility Medicine Ledger',next:'Near-Expiry Medicine Ledger (FEFO Protocol)'},
 {Page:WorkforcePage,destination:'/facility/attendance',initial:'Staff role catalogue',next:'Attendance Records'},
 {Page:EquipmentPage,destination:'/facility/ambulance',initial:'Equipment register',next:'Ambulance register'},
])('updates the active tab when navigating to $destination without remounting',async({Page,destination,initial,next})=>{
 renderData(<><Link to={destination}>Change route</Link><Page/></>);
 await screen.findByText(initial);fireEvent.click(screen.getByRole('link',{name:'Change route'}));
 expect(await screen.findByText(next)).toBeInTheDocument();
});

it('exposes authorized shared workflows without granting administrator capabilities',()=>{
 authenticate(['inventory.read','procurement.read','reports.read'],'restricted');
 const user=useAuthStore.getState().user!;useAuthStore.setState({role:'FACILITY_ADMIN',user:{...user,role:'FACILITY_ADMIN',backendRoles:['dev_data_inventory']}});
 renderData(<RoleSidebar/>);
 expect(screen.getByRole('link',{name:'Supply Chain'})).toHaveAttribute('href','/warehouses');
 expect(screen.getByRole('link',{name:'Resource Map'})).toHaveAttribute('href','/map');
 expect(screen.getByRole('link',{name:'Reports & Analytics'})).toHaveAttribute('href','/analytics');
 expect(screen.queryByRole('link',{name:'Bed Availability'})).toBeNull();
 expect(screen.queryByRole('link',{name:'Users & Personnel'})).toBeNull();
 expect(screen.getByText('dev_data_inventory')).toBeInTheDocument();
});
