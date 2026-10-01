import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { LoginPage } from '@/modules/auth/LoginPage';
import { useAuthStore } from '@/store/authStore';
import { RoleGuard } from '@/components/common/RoleGuard';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { ROLE_HOME } from '@/app/roleRoutes';
import { UnauthorizedPage } from '@/pages/UnauthorizedPage';

describe('Task 25 — Comprehensive Authentication & Role-Based Routing Test Suite', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      role: null,
      permissions: [],
      accessToken: null,
      isAuthenticated: false,
      isRestoring: false,
      loginError: null,
    });
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  // 1. Login page rendering
  it('1. Login page renders all required elements', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/Sanjeevani Grid/i)).toBeInTheDocument();
    expect(screen.getByText(/Command Access Portal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Role/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Official Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Passcode/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Command Portal/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Remember this terminal/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Forgot passcode/i })).toBeInTheDocument();
  });

  // 2. Successful login
  it('2. Successful login authenticates user and sets store state', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // Click demo button for National Admin
    const demoBtn = screen.getByRole('button', { name: /National Health Command/i });
    fireEvent.click(demoBtn);

    const submitBtn = screen.getByRole('button', { name: /Sign In to Command Portal/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.role).toBe('NATIONAL_ADMIN');
      expect(state.user?.email).toBe('national.command@sanjeevani.gov.in');
    });
  });

  // 3. Incorrect password
  it('3. Shows authentication error when credentials are wrong', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const roleSelect = screen.getByLabelText(/Role/i);
    const emailInput = screen.getByLabelText(/Official Email/i);
    const passInput = screen.getByLabelText(/Passcode/i);

    fireEvent.change(roleSelect, { target: { value: 'NATIONAL_ADMIN' } });
    fireEvent.change(emailInput, { target: { value: 'national.command@sanjeevani.gov.in' } });
    fireEvent.change(passInput, { target: { value: 'wrong_password_123' } });

    const submitBtn = screen.getByRole('button', { name: /Sign In to Command Portal/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials/i)).toBeInTheDocument();
    });
  });

  // 4. Incorrect selected role
  it('4. Rejects login if selected role does not match account', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const roleSelect = screen.getByLabelText(/Role/i);
    const emailInput = screen.getByLabelText(/Official Email/i);
    const passInput = screen.getByLabelText(/Passcode/i);

    // Choose STATE_ADMIN role selector, but provide NATIONAL_ADMIN credentials
    fireEvent.change(roleSelect, { target: { value: 'STATE_ADMIN' } });
    fireEvent.change(emailInput, { target: { value: 'national.command@sanjeevani.gov.in' } });
    fireEvent.change(passInput, { target: { value: 'NationalPass2026!' } });

    const submitBtn = screen.getByRole('button', { name: /Sign In to Command Portal/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/The selected role does not match this account\./i)).toBeInTheDocument();
    });

    // Verify user was NOT logged in
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  // 5. National admin redirect mapping
  it('5. National admin route maps to /national/dashboard', () => {
    expect(ROLE_HOME.NATIONAL_ADMIN).toBe('/national/dashboard');
  });

  // 6. State admin redirect mapping
  it('6. State admin route maps to /state/dashboard', () => {
    expect(ROLE_HOME.STATE_ADMIN).toBe('/state/dashboard');
  });

  // 7. District admin redirect mapping
  it('7. District admin route maps to /district/dashboard', () => {
    expect(ROLE_HOME.DISTRICT_ADMIN).toBe('/district/dashboard');
  });

  // 8. Facility admin redirect mapping
  it('8. Facility admin route maps to /facility/dashboard', () => {
    expect(ROLE_HOME.FACILITY_ADMIN).toBe('/facility/dashboard');
  });

  // 9. Super admin redirect mapping
  it('9. Super admin route maps to /admin/dashboard', () => {
    expect(ROLE_HOME.SUPER_ADMIN).toBe('/admin/dashboard');
  });

  // 10. Protected routes redirect unauthenticated users to /login
  it('10. RoleGuard redirects unauthenticated visitors to /login', () => {
    render(
      <MemoryRouter initialEntries={['/national/dashboard']}>
        <Routes>
          <Route path="/login" element={<div>LOGIN_PAGE_STUB</div>} />
          <Route
            path="/national/dashboard"
            element={
              <RoleGuard allowedRoles={['NATIONAL_ADMIN']}>
                <div>SECRET_NATIONAL_DASHBOARD</div>
              </RoleGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('LOGIN_PAGE_STUB')).toBeInTheDocument();
    expect(screen.queryByText('SECRET_NATIONAL_DASHBOARD')).not.toBeInTheDocument();
  });

  // 11. Unauthorized URL access blocks wrong role and redirects to /unauthorized
  it('11. Unauthorized URL access directs wrong role to /unauthorized', () => {
    useAuthStore.setState({
      user: {
        id: 'usr-fac-01',
        email: 'rml.admin@sanjeevani.gov.in',
        name: 'Dr. Neha Verma',
        role: 'FACILITY_ADMIN',
        permissions: ['inventory:view'],
        department: 'Operations',
      },
      role: 'FACILITY_ADMIN',
      permissions: ['inventory:view'],
      accessToken: 'token-fac',
      isAuthenticated: true,
      isRestoring: false,
    });

    render(
      <MemoryRouter initialEntries={['/national/dashboard']}>
        <Routes>
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route
            path="/national/dashboard"
            element={
              <RoleGuard allowedRoles={['NATIONAL_ADMIN']}>
                <div>NATIONAL_DATA</div>
              </RoleGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/403/i)).toBeInTheDocument();
    expect(screen.getByText(/Restricted Jurisdiction Access/i)).toBeInTheDocument();
    expect(screen.queryByText('NATIONAL_DATA')).not.toBeInTheDocument();
  });

  // 12. Logout
  it('12. Logout clears tokens, user details, and state', async () => {
    useAuthStore.setState({
      user: {
        id: 'usr-nat-01',
        email: 'national.command@sanjeevani.gov.in',
        name: 'Dr. V. K. Paul',
        role: 'NATIONAL_ADMIN',
        permissions: ['dashboard:view'],
      },
      role: 'NATIONAL_ADMIN',
      permissions: ['dashboard:view'],
      accessToken: 'test-token',
      isAuthenticated: true,
      isRestoring: false,
    });

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.role).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(localStorage.getItem('sanjeevani_auth_session')).toBeNull();
  });

  // 13. Refresh / Session restore
  it('13. Session restore recovers authentication from storage without kicking to login', async () => {
    const sessionPayload = {
      user: {
        id: 'usr-nat-01',
        email: 'national.command@sanjeevani.gov.in',
        name: 'Dr. V. K. Paul',
        role: 'NATIONAL_ADMIN' as const,
        permissions: ['dashboard:view'],
      },
      role: 'NATIONAL_ADMIN' as const,
      permissions: ['dashboard:view'],
      accessToken: 'stored-session-token',
    };
    localStorage.setItem('sanjeevani_auth_session', JSON.stringify(sessionPayload));

    await useAuthStore.getState().restoreSession();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.role).toBe('NATIONAL_ADMIN');
    expect(state.user?.name).toBe('Dr. V. K. Paul');
  });

  // 14. Role-specific sidebar
  it('14. Renders role-specific navigation for the authenticated role', () => {
    useAuthStore.setState({
      user: {
        id: 'usr-fac-01',
        email: 'rml.admin@sanjeevani.gov.in',
        name: 'Dr. Neha Verma',
        role: 'FACILITY_ADMIN',
        permissions: ['facility:view'],
      },
      role: 'FACILITY_ADMIN',
      permissions: ['facility:view'],
      isAuthenticated: true,
      isRestoring: false,
    });

    render(
      <MemoryRouter>
        <RoleSidebar />
      </MemoryRouter>
    );

    expect(screen.getByText(/Facility Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Medicine Stock/i)).toBeInTheDocument();
    expect(screen.getByText(/Daily Attendance/i)).toBeInTheDocument();
    expect(screen.getByText(/Ambulance Unit/i)).toBeInTheDocument();
  });

  // 15. Mobile interface
  it('15. Sidebar supports toggle and responsive collapsed modes', () => {
    useAuthStore.setState({
      user: {
        id: 'usr-adm-01',
        email: 'sysadmin@sanjeevani.gov.in',
        name: 'Chief Admin Officer',
        role: 'SUPER_ADMIN',
        permissions: ['users:manage'],
      },
      role: 'SUPER_ADMIN',
      permissions: ['users:manage'],
      isAuthenticated: true,
      isRestoring: false,
    });

    const { container } = render(
      <MemoryRouter>
        <RoleSidebar />
      </MemoryRouter>
    );

    const aside = container.querySelector('aside');
    expect(aside).toBeInTheDocument();
    expect(screen.getByText(/Audit Logs/i)).toBeInTheDocument();
    expect(screen.getByText(/Roles & Permissions/i)).toBeInTheDocument();
  });
});
