import React from 'react';
import { afterEach, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/modules/auth/LoginPage';
import { useAuthStore } from '@/store/authStore';
import { apiRequest, publicRequest, readSession, saveTokens, clearSession } from '@/services/httpClient';

// Opt-in real HTTP checks. No fetch mocks, transport overrides, or fake tokens.
const enabled = process.env.AUTH_LIVE_TEST === '1';
const outage = process.env.AUTH_LIVE_OUTAGE === '1';
afterEach(() => { cleanup(); clearSession(); });
function submit(username: string, password: string) {
  useAuthStore.setState({ isRestoring: false, isLoading: false, error: null });
  render(<MemoryRouter><LoginPage /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText('Official Email / Username'), { target: { value: username } });
  fireEvent.change(screen.getByLabelText('Passcode / Password'), { target: { value: password } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign In to Command Portal' }));
}

it.skipIf(!enabled || outage)('real frontend form -> live JWT -> current user -> protected endpoint -> refresh -> logout', async () => {
  expect(process.env.AUTH_LIVE_USERNAME).toBeTruthy(); expect(process.env.AUTH_LIVE_PASSWORD).toBeTruthy();
  const health = await publicRequest('/api/v1/health'); expect(health).toBeTruthy();
  submit(process.env.AUTH_LIVE_USERNAME!, process.env.AUTH_LIVE_PASSWORD!);
  await waitFor(() => expect(useAuthStore.getState().isAuthenticated).toBe(true), { timeout: 10000 });
  const session = readSession()!;
  expect(session.accessToken.split('.')).toHaveLength(3);
  const claims = JSON.parse(atob(session.accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
  expect(claims.type).toBe('access'); expect(claims.iss).toBe('sanjeevani'); expect(claims.sid).toBeTruthy();
  const me = await apiRequest<{ data: { id: string; username: string; roles: string[] } }>('/api/v1/users/me');
  expect(me.data.id).toBe(claims.sub); expect(me.data.username).toBe(process.env.AUTH_LIVE_USERNAME);
  expect(me.data.roles).toContain('administrator');
  const users = await apiRequest<{ data: { username: string }[] }>('/api/v1/users');
  expect(users.data.some(user => user.username === process.env.AUTH_LIVE_USERNAME)).toBe(true);
  saveTokens({ access_token: session.accessToken, refresh_token: session.refreshToken, token_type: 'bearer', expires_in: 1 }, false);
  await apiRequest('/api/v1/users/me');
  const rotated = readSession()!; expect(rotated.refreshToken).not.toBe(session.refreshToken);
  await useAuthStore.getState().logout(); expect(readSession()).toBeNull();
  await expect(publicRequest('/api/v1/users/me', { headers: { Authorization: `Bearer ${rotated.accessToken}` } })).rejects.toMatchObject({ status: 401 });
}, 20000);

it.skipIf(!enabled || outage)('live backend rejects incorrect and former demo credentials in the frontend', async () => {
  for (const [username, password] of [[process.env.AUTH_LIVE_USERNAME!, 'incorrect-password'], ['national.command@sanjeevani.gov.in', 'NationalPass2026!']]) {
    submit(username, password);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Invalid credentials/i), { timeout: 10000 });
    expect(readSession()).toBeNull(); expect(useAuthStore.getState().isAuthenticated).toBe(false); cleanup();
  }
}, 20000);

it.skipIf(!enabled || !outage)('stopped backend produces a visible error, never a demo session', async () => {
  submit('national.command@sanjeevani.gov.in', 'NationalPass2026!');
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the backend'), { timeout: 20000 });
  expect(useAuthStore.getState().isAuthenticated).toBe(false); expect(readSession()).toBeNull();
}, 25000);
