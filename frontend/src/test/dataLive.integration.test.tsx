import React from 'react';
import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { LoginPage } from '@/modules/auth/LoginPage';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { ReportsPanel } from '@/modules/analytics/ReportsPanel';
import { useAuthStore } from '@/store/authStore';
import { apiRequest, clearSession, readSession } from '@/services/httpClient';
import { getData, sendData } from '@/services/dataApi';

// Explicit opt-in. Transport, tokens, services and data are NOT mocked.
// Only the shared test setup substitutes Leaflet rendering; these tests use no map.
const enabled = process.env.DATA_LIVE_TEST === '1';
const fixture = JSON.parse(process.env.DATA_LIVE_FIXTURE || '{}');
const clients: QueryClient[] = [];
function renderLive(ui: React.ReactElement, route = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter></QueryClientProvider>);
}
async function signIn() {
  expect(process.env.AUTH_LIVE_USERNAME).toBeTruthy(); expect(process.env.AUTH_LIVE_PASSWORD).toBeTruthy();
  expect(fixture.database).toBe('sanjeevani_dev');
  useAuthStore.setState({ isRestoring: false, isLoading: false, error: null });
  renderLive(<LoginPage />);
  fireEvent.change(screen.getByLabelText('Official Email / Username'), { target: { value: process.env.AUTH_LIVE_USERNAME } });
  fireEvent.change(screen.getByLabelText('Passcode / Password'), { target: { value: process.env.AUTH_LIVE_PASSWORD } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign In to Command Portal' }));
  await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(true), { timeout: 10000 });
  expect(readSession()!.accessToken.split('.')).toHaveLength(3);
  cleanup();
}
/** Independent SQL read proves the live API records are in persistent PostgreSQL. */
function databaseRecord() {
  const backend = path.resolve(process.cwd(), '../backend');
  const python = path.join(backend, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
  const script = `
import asyncio,json,sys
from uuid import UUID
from sqlalchemy import text,select
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.database import AsyncSessionLocal,engine
from app.models import Facility,Inventory
from app.models.operations import BedCapacity
async def main():
 assert settings.APP_ENV=='development' and make_url(settings.get_database_url()).database=='sanjeevani_dev'
 async with AsyncSessionLocal() as db:
  assert await db.scalar(text('SELECT current_database()'))=='sanjeevani_dev'
  facility=await db.get(Facility,UUID(sys.argv[1]));assert facility.code=='DEV-PHASE3'
  bed=await db.scalar(select(BedCapacity).where(BedCapacity.facility_id==facility.id,BedCapacity.bed_type=='DEV-PHASE3 ICU'))
  stock=await db.get(Inventory,UUID(sys.argv[2]));assert stock.facility_id==facility.id
  print(json.dumps({'facility_name':facility.name,'quantity':stock.quantity,'bed_capacity':bed.capacity,'bed_occupied':bed.occupied}))
 await engine.dispose()
asyncio.run(main())
`;
  return JSON.parse(execFileSync(python, ['-c', script, fixture.facility_id, fixture.inventory_id], { cwd: backend, encoding: 'utf8' }));
}
afterEach(() => { cleanup(); clients.forEach(c => c.clear()); clients.length = 0; clearSession(); });

it.skipIf(!enabled)('LIVE React login -> JWT -> facilities HTTP -> PostgreSQL -> rendered facility metadata', async () => {
  await signIn(); const stored = databaseRecord();
  renderLive(<FacilitiesPage />);
  expect(await screen.findByText(stored.facility_name, {}, { timeout: 10000 })).toBeInTheDocument();
  expect(screen.getByText('22.5, 88.3')).toBeInTheDocument();
  expect((await screen.findAllByText(/DEVELOPMENT ONLY Phase 3 blocks/)).length).toBeGreaterThan(0);
}, 30000);

it.skipIf(!enabled)('LIVE inventory, expiry and safety stock render real PostgreSQL records', async () => {
  await signIn(); const stored = databaseRecord();
  renderLive(<InventoryPage />, `/inventory?facility_id=${fixture.facility_id}`);
  await screen.findByText(fixture.medicine_name, {}, { timeout: 10000 });
  expect(screen.getByText('DEV-PHASE3-BATCH')).toBeInTheDocument();
  expect(screen.getAllByText(String(stored.quantity)).length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole('button', { name: 'Expiry Tracker' }));
  expect(await screen.findByText('upcoming')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Days of Stock & Safety' }));
  await screen.findByRole('option', { name: `${fixture.medicine_name} (test-unit)` });
  fireEvent.change(screen.getByLabelText('Medicine'), { target: { value: fixture.medicine_id } });
  const calculation = await getData<{status:string;days_of_stock:number|null}>('/inventory/days-of-stock', {facility_id:fixture.facility_id,medicine_id:fixture.medicine_id});
  expect(calculation.days_of_stock).toBeNull();
  await screen.findByText(calculation.status); expect(screen.getByText('10')).toBeInTheDocument();
}, 30000);

it.skipIf(!enabled)('LIVE controlled backend change -> PostgreSQL -> refetch -> changed bed rendering, then restores seed value', async () => {
  await signIn(); const before = databaseRecord();
  const changed = before.bed_occupied === 4 ? 5 : 4;
  renderLive(<BedsPage />); await screen.findByRole('option', { name: `${fixture.facility_name} (DEV-PHASE3)` });
  fireEvent.change(screen.getByLabelText('Facility'), { target: { value: fixture.facility_id } });
  await screen.findByText(`${before.bed_capacity - before.bed_occupied} available`);
  try {
    await sendData('/beds', 'PUT', { facility_id: fixture.facility_id, bed_type: 'DEV-PHASE3 ICU', capacity: before.bed_capacity, occupied: changed });
    expect(databaseRecord().bed_occupied).toBe(changed);
    fireEvent.click(screen.getByRole('button', { name: 'Refresh beds' }));
    await screen.findByText(`${before.bed_capacity - changed} available`);
  } finally {
    await sendData('/beds', 'PUT', { facility_id: fixture.facility_id, bed_type: 'DEV-PHASE3 ICU', capacity: before.bed_capacity, occupied: before.bed_occupied });
    expect(databaseRecord().bed_occupied).toBe(before.bed_occupied);
  }
}, 30000);

it.skipIf(!enabled)('LIVE alerts and procurement views render existing backend records without simulated actions', async () => {
  await signIn();
  const alerts = await getData<{ id: string }[]>('/alerts'); expect(alerts.some(a => fixture.alert_ids.includes(a.id))).toBe(true);
  renderLive(<AlertsPage />); expect((await screen.findAllByText('LOW_STOCK', {}, { timeout: 10000 })).length).toBeGreaterThan(0);
  cleanup(); renderLive(<WarehouseDashboardPage />);
  fireEvent.click(screen.getByRole('button', { name: 'Suppliers', exact: true }));
  await screen.findByText('DEVELOPMENT ONLY Phase 3 Supplier');
  fireEvent.click(screen.getByRole('button', { name: 'Procurement', exact: true }));
  await screen.findByText('DEV-PHASE3-ORDER'); expect(screen.getByText('draft')).toBeInTheDocument();
}, 30000);

it.skipIf(!enabled)('LIVE report React rendering and authenticated CSV/PDF/XLSX bytes come from the real backend', async () => {
  await signIn(); renderLive(<ReportsPanel />);
  await screen.findByText(fixture.medicine_name, {}, { timeout: 10000 });
  for (const format of ['csv', 'pdf', 'xlsx']) {
    const blob = await apiRequest<Blob>(`/api/v1/reports/stock?facility_id=${fixture.facility_id}&format=${format}`, {}, 'blob');
    expect(blob.size).toBeGreaterThan(50);
    const bytes = new Uint8Array(await blob.arrayBuffer());
    if (format === 'pdf') expect(new TextDecoder().decode(bytes.slice(0, 4))).toBe('%PDF');
    if (format === 'xlsx') expect(Array.from(bytes.slice(0, 2))).toEqual([80, 75]);
    if (format === 'csv') expect(new TextDecoder().decode(bytes)).toContain(fixture.medicine_name);
  }
}, 30000);
