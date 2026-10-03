import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LoginPage } from '@/modules/auth/LoginPage';
import { RoleGuard } from '@/components/common/RoleGuard';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { apiRequest, publicRequest, clearSession, readSession, saveTokens, SESSION_KEY } from '@/services/httpClient';
import { canAccessPath } from '@/app/authorization';
import { getRoleHomeRoute } from '@/app/roleRoutes';
import { ForgotPasswordPage } from '@/modules/auth/ForgotPasswordPage';
import { MFAPage } from '@/modules/auth/MFAPage';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';
import { useUIStore } from '@/store/uiStore';

const tokens = { access_token: 'backend-access', refresh_token: 'backend-refresh', token_type: 'bearer' as const, expires_in: 900 };
const profile = { id: 'real-user-id', username: 'admin', active: true, roles: ['administrator'],
  permissions: ['admin.users', 'inventory.read'], scope_mode: 'global', facility_ids: [], district_ids: [] };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
const fetchMock = vi.fn();
const credentials = { email: 'admin', password: 'correct-password' };
it('aborts a timed-out request without inventing a session or success', async () => {
  vi.useFakeTimers();
  fetchMock.mockImplementation((_url, init) => new Promise((_resolve, reject) => {
    init.signal.addEventListener('abort', () => reject(new DOMException('Timed out', 'AbortError')));
  }));
  try {
    const pending = expect(publicRequest('/api/v1/health')).rejects.toThrow('Cannot reach the backend');
    await vi.advanceTimersByTimeAsync(15001);
    await pending;
    expect(readSession()).toBeNull();
  } finally { vi.useRealTimers(); }
});
beforeEach(() => {
  localStorage.clear(); sessionStorage.clear(); clearSession();
  useAuthStore.setState({ user: null, role: null, permissions: [], accessToken: null, isAuthenticated: false,
    isRestoring: false, isLoading: false, error: null });
  fetchMock.mockReset(); vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function mockLogin(user = profile) {
  fetchMock.mockResolvedValueOnce(response(tokens)).mockResolvedValueOnce(response({ success: true, data: user }));
}

describe('backend authentication contract', () => {
  it('offers only provisioned portal categories, with backend-authoritative access', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    const selector = screen.getByLabelText('Role') as HTMLSelectElement;
    expect(Array.from(selector.options).map(option => option.value)).toEqual(['', 'SUPER_ADMIN', 'FACILITY_ADMIN']);
    expect(screen.getByText(/National, state and district portals have no provisioned role profiles/)).toBeInTheDocument();
  });
  it.each(['dev_data_operator', 'dev_data_inventory', 'dev_data_reader'])('maps %s without inventing grants', async role => {
    mockLogin({ ...profile, roles: [role], permissions: ['inventory.read'], scope_mode: 'restricted', facility_ids: ['source-facility'] });
    const identity = await authService.login(credentials);
    expect(identity.role).toBe('FACILITY_ADMIN');
    expect(identity.user.backendPermissions).toEqual(['inventory.read']);
    expect(identity.user.facilityIds).toEqual(['source-facility']);
    expect(identity.permissions).toEqual(['inventory:view']);
  });
  it('sends form credentials and loads identity and grants with the real access token', async () => {
    mockLogin();
    expect(await useAuthStore.getState().login(credentials)).toBe('/admin/dashboard');
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/auth\/login$/);
    expect(options.headers['Content-Type']).toBe('application/x-www-form-urlencoded');
    expect(options.body.get('username')).toBe('admin');
    expect(options.body.get('password')).toBe('correct-password');
    expect(options.body.has('role')).toBe(false);
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/api\/v1\/users\/me$/);
    expect(fetchMock.mock.calls[1][1].headers.get('Authorization')).toBe('Bearer backend-access');
    expect(useAuthStore.getState().user?.id).toBe('real-user-id');
    expect(useAuthStore.getState().hasPermission('inventory:view')).toBe(true);
    expect(useAuthStore.getState().hasPermission('system:config')).toBe(false);
    expect(localStorage.getItem(SESSION_KEY)).toBeNull();
    expect(JSON.parse(sessionStorage.getItem(SESSION_KEY)!)).not.toHaveProperty('user');
  });
  it('persists only tokens when remember is selected, then re-fetches server identity', async () => {
    mockLogin(); await authService.login({ ...credentials, rememberMe: true });
    expect(sessionStorage.getItem(SESSION_KEY)).toBeNull();
    fetchMock.mockResolvedValueOnce(response({ data: { ...profile, permissions: [] } }));
    expect(await useAuthStore.getState().restoreSession()).toBe(true);
    expect(useAuthStore.getState().permissions).toEqual([]);
  });
  it.each([401, 422, 503])('fails closed on HTTP %s, even for former demo credentials', async status => {
    fetchMock.mockResolvedValueOnce(response({ error: { message: 'Invalid credentials' } }, status));
    await expect(useAuthStore.getState().login({ email: 'national.command@sanjeevani.gov.in', password: 'NationalPass2026!' })).rejects.toThrow();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(readSession()).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().error).toMatch(status === 503 ? /unavailable/i : status === 422 ? /fields/i : /credentials/i);
  });
  it('reports a network outage, never accepting a demo account', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await expect(useAuthStore.getState().login({ email: 'national.command@sanjeevani.gov.in', password: 'NationalPass2026!' })).rejects.toThrow('Cannot reach');
    expect(readSession()).toBeNull(); expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
  it('rejects a selected role that the server did not assign', async () => {
    mockLogin(); await expect(authService.login({ ...credentials, role: 'NATIONAL_ADMIN' })).rejects.toThrow('not assigned');
    expect(readSession()).toBeNull();
  });
  it.each(['unknown', 'constructor', '__proto__'])('rejects unsupported role %s without defaulting to an administrator', async name => {
    mockLogin({ ...profile, roles: [name] });
    await expect(authService.login(credentials)).rejects.toThrow('not assigned');
  });
  it('does not restore legacy or forged stored identity', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify({ accessToken: 'sg_jwt_super_admin_123', role: 'SUPER_ADMIN', user: profile }));
    expect(await useAuthStore.getState().restoreSession()).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled(); expect(localStorage.getItem(SESSION_KEY)).toBeNull();
  });
  it('fails restoration when the backend cannot verify the stored token', async () => {
    saveTokens(tokens, true); fetchMock.mockRejectedValue(new TypeError('offline'));
    expect(await useAuthStore.getState().restoreSession()).toBe(false);
    expect(useAuthStore.getState().error).toMatch(/Cannot reach/); expect(readSession()).toBeNull();
  });
  it('rotates expired tokens once for concurrent protected requests', async () => {
    saveTokens({ ...tokens, expires_in: 1 }, false);
    fetchMock.mockImplementation(async (url: string) => url.endsWith('/auth/refresh')
      ? response({ data: { ...tokens, access_token: 'new-access', refresh_token: 'new-refresh' } }) : response({ data: [] }));
    await Promise.all([apiRequest('/api/v1/users'), apiRequest('/api/v1/users')]);
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/auth/refresh'))).toHaveLength(1);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ refresh_token: 'backend-refresh' });
    expect(fetchMock.mock.calls[1][1].headers.get('Authorization')).toBe('Bearer new-access');
    expect(readSession()?.refreshToken).toBe('new-refresh');
  });
  it('refreshes a server-rejected access token and retries once', async () => {
    saveTokens(tokens, false);
    fetchMock.mockResolvedValueOnce(response({}, 401)).mockResolvedValueOnce(response({ data: { ...tokens, access_token: 'new' } }))
      .mockResolvedValueOnce(response({ data: [] }));
    await apiRequest('/api/v1/users'); expect(fetchMock).toHaveBeenCalledTimes(3);
  });
  it('uses the browser lock to share a rotation across tabs', async () => {
    saveTokens({ ...tokens, expires_in: 1 }, true);
    const lock = vi.fn(async (_name, callback) => {
      // Another tab rotates before this tab acquires the exclusive lock.
      saveTokens({ ...tokens, access_token: 'other-tab-access', refresh_token: 'other-tab-refresh' }, true);
      return await callback();
    });
    vi.stubGlobal('navigator', { locks: { request: lock } });
    fetchMock.mockResolvedValueOnce(response({ data: [] }));
    await apiRequest('/api/v1/users');
    expect(lock).toHaveBeenCalledTimes(1); expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][1].headers.get('Authorization')).toBe('Bearer other-tab-access');
  });
  it('clears expired sessions when refresh is rejected', async () => {
    saveTokens({ ...tokens, expires_in: 1 }, false); fetchMock.mockResolvedValueOnce(response({}, 401));
    await expect(apiRequest('/api/v1/users')).rejects.toThrow(); expect(readSession()).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
  it('does not refresh or elevate a forbidden request', async () => {
    saveTokens(tokens, false); fetchMock.mockResolvedValueOnce(response({ error: { message: 'Permission denied' } }, 403));
    await expect(apiRequest('/api/v1/users')).rejects.toThrow('Permission denied');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it('logs out with bearer credentials and clears session and identity', async () => {
    mockLogin(); await useAuthStore.getState().login(credentials);
    fetchMock.mockResolvedValueOnce(response({ data: null })); await useAuthStore.getState().logout();
    expect(fetchMock.mock.calls[2][0]).toMatch(/\/auth\/logout$/);
    expect(fetchMock.mock.calls[2][1].headers.get('Authorization')).toBe('Bearer backend-access');
    expect(readSession()).toBeNull(); expect(useAuthStore.getState().user).toBeNull();
  });
  it('cleans up locally and warns when logout cannot revoke remotely', async () => {
    mockLogin(); await useAuthStore.getState().login(credentials); fetchMock.mockRejectedValueOnce(new TypeError('offline'));
    await useAuthStore.getState().logout(); expect(readSession()).toBeNull();
    expect(useAuthStore.getState().error).toMatch(/could not confirm/);
  });
  it('does not resurrect a session when logout races a pending login', async () => {
    let resolve!: (value: Response) => void;
    fetchMock.mockImplementationOnce(() => new Promise<Response>(done => { resolve = done; }));
    const login = useAuthStore.getState().login(credentials);
    await useAuthStore.getState().logout(); resolve(response(tokens));
    await expect(login).rejects.toThrow('cancelled'); expect(readSession()).toBeNull();
  });
  it('does not resurrect tokens when clearing a session races refresh', async () => {
    saveTokens({ ...tokens, expires_in: 1 }, false);
    let resolve!: (value: Response) => void;
    fetchMock.mockImplementationOnce(() => new Promise<Response>(done => { resolve = done; }));
    const pending = apiRequest('/api/v1/users');
    clearSession(); resolve(response({ data: tokens }));
    await expect(pending).rejects.toThrow('Session ended'); expect(readSession()).toBeNull();
  });
  it('fails closed if current-user validation fails after token issuance', async () => {
    fetchMock.mockResolvedValueOnce(response(tokens)).mockResolvedValueOnce(response({}, 503));
    await expect(useAuthStore.getState().login(credentials)).rejects.toThrow('unavailable');
    expect(readSession()).toBeNull(); expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
  it('forwards optional MFA proof to backend verification', async () => {
    mockLogin(); await authService.login({ ...credentials, mfaProof: 'verification-proof' });
    expect(fetchMock.mock.calls[0][1].body.get('mfa_proof')).toBe('verification-proof');
  });
});

describe('login UI and navigation', () => {
  it('has empty credentials, no demo presets, and submits the actual form', async () => {
    mockLogin();
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    expect(screen.queryByText(/Fast Role Demo/)).toBeNull();
    expect(screen.getByLabelText('Official Email / Username')).toHaveValue('');
    fireEvent.change(screen.getByLabelText('Official Email / Username'), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText('Passcode / Password'), { target: { value: 'correct-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In to Command Portal' }));
    await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(true));
  });
  it('shows an outage in the login page', async () => {
    fetchMock.mockRejectedValue(new TypeError('offline'));
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Official Email / Username'), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText('Passcode / Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In to Command Portal' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the backend');
  });
  it('redirects unauthenticated protected navigation', () => {
    render(<MemoryRouter initialEntries={['/admin/users']}><Routes>
      <Route path="/admin/users" element={<RoleGuard><div>private</div></RoleGuard>} />
      <Route path="/login" element={<div>sign in required</div>} /></Routes></MemoryRouter>);
    expect(screen.getByText('sign in required')).toBeInTheDocument();
  });
  it('blocks direct navigation without the required server permission, including SUPER_ADMIN', async () => {
    mockLogin({ ...profile, permissions: [] }); await useAuthStore.getState().login(credentials);
    render(<MemoryRouter initialEntries={['/admin/users']}><Routes>
      <Route path="/admin/users" element={<RoleGuard><div>private</div></RoleGuard>} />
      <Route path="/unauthorized" element={<div>forbidden</div>} /></Routes></MemoryRouter>);
    expect(screen.getByText('forbidden')).toBeInTheDocument(); expect(screen.queryByText('private')).toBeNull();
  });
  it('hides unauthorized sidebar links and limits global administration by server scope', async () => {
    mockLogin(); await useAuthStore.getState().login(credentials);
    render(<MemoryRouter><RoleSidebar /></MemoryRouter>);
    expect(screen.getByText('Users & Personnel')).toBeInTheDocument(); expect(screen.queryByText('Audit Logs')).toBeNull();
    expect(canAccessPath('/admin/users', { ...useAuthStore.getState().user!, scopeMode: 'restricted' })).toBe(false);
  });
  it('does not accept the simulated UI role as authentication in the legacy guard', () => {
    useUIStore.setState({ activeRole: 'national_officer' });
    render(<MemoryRouter initialEntries={['/national/dashboard']}><Routes>
      <Route path="/national/dashboard" element={<ProtectedRoute allowedRoles={['national_officer']} />} />
      <Route path="/login" element={<div>sign in required</div>} /></Routes></MemoryRouter>);
    expect(screen.getByText('sign in required')).toBeInTheDocument();
  });
  it('blocks the wrong portal role even with a screen capability', async () => {
    mockLogin({ ...profile, roles: ['facility_admin'], permissions: ['reports.read'] });
    await useAuthStore.getState().login(credentials);
    render(<MemoryRouter initialEntries={['/national/dashboard']}><Routes>
      <Route path="/national/dashboard" element={<RoleGuard allowedRoles={['NATIONAL_ADMIN']}><div>private</div></RoleGuard>} />
      <Route path="/unauthorized" element={<div>forbidden</div>} /></Routes></MemoryRouter>);
    expect(screen.getByText('forbidden')).toBeInTheDocument();
  });
  it('never reports recovery success when the backend is unavailable', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('offline'));
    render(<MemoryRouter><ForgotPasswordPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'admin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Request recovery' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the backend');
    expect(screen.queryByText(/If the account is eligible/)).toBeNull();
  });
  it('submits recovery to the real endpoint and gives a non-enumerating message', async () => {
    fetchMock.mockResolvedValueOnce(response({ success: true, data: { message: 'If eligible' } }, 202));
    render(<MemoryRouter><ForgotPasswordPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'admin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Request recovery' }));
    expect(await screen.findByText(/If the account is eligible/)).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/auth\/password\/reset\/request$/);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ username: 'admin' });
  });
  it('does not offer simulated MFA success or issue a session', () => {
    render(<MemoryRouter><MFAPage /></MemoryRouter>);
    expect(screen.getByText(/backend must verify/)).toBeInTheDocument();
    expect(screen.queryByRole('button')).toBeNull(); expect(readSession()).toBeNull();
  });
  it.each([['SUPER_ADMIN', '/admin/dashboard'], ['NATIONAL_ADMIN', '/national/dashboard'], ['STATE_ADMIN', '/state/dashboard'],
    ['DISTRICT_ADMIN', '/district/dashboard'], ['FACILITY_ADMIN', '/facility/dashboard']] as const)('maps %s to its home', (role, path) => {
    expect(getRoleHomeRoute(role)).toBe(path);
  });
});
