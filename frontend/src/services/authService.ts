import { AuthResponse, LoginRequest, Permission, Role } from '@/types/auth';
import { apiRequest, publicRequest, readSession, saveTokens, clearSession, TokenPair } from './httpClient';

// Presentation aliases only. A mapped role NEVER supplies permissions.
export const BACKEND_ROLES: Record<string, Role> = {
  administrator: 'SUPER_ADMIN', admin: 'SUPER_ADMIN', super_admin: 'SUPER_ADMIN',
  national_admin: 'NATIONAL_ADMIN', national_officer: 'NATIONAL_ADMIN',
  state_admin: 'STATE_ADMIN', state_officer: 'STATE_ADMIN',
  district_admin: 'DISTRICT_ADMIN', district_officer: 'DISTRICT_ADMIN', facility_admin: 'FACILITY_ADMIN',
};
const CAPABILITIES: Partial<Record<Permission, string>> = {
  'dashboard:view': 'reports.read', 'inventory:view': 'inventory.read', 'inventory:update': 'inventory.write',
  'beds:view': 'beds.read', 'beds:update': 'beds.write', 'workforce:view': 'workforce.read',
  'analytics:view': 'reports.read', 'alerts:view': 'alerts.read', 'emergency:view': 'emergency.activate',
  'emergency:override': 'emergency.activate', 'federated:manage': 'federation.manage',
  'users:manage': 'admin.users', 'roles:manage': 'admin.users', 'system:config': 'admin.config',
  'facility:view': 'facility.manage',
};
export interface BackendUser {
  id: string; username: string; active: boolean; scope_mode: string;
  roles: string[]; permissions: string[]; facility_ids: string[]; district_ids: string[];
}
let revision = 0;
let restoring: Promise<AuthResponse | null> | null = null;
async function currentIdentity(selectedRole?: Role): Promise<AuthResponse> {
  const { data: profile } = await apiRequest<{ data: BackendUser }>('/api/v1/users/me');
  if (!profile.active || !Array.isArray(profile.roles) || !Array.isArray(profile.permissions))
    throw new Error('The backend returned an invalid user profile.');
  const roles = profile.roles.map(name => Object.prototype.hasOwnProperty.call(BACKEND_ROLES, name.toLowerCase())
    ? BACKEND_ROLES[name.toLowerCase()] : undefined).filter((role): role is Role => !!role);
  const role = selectedRole || roles[0];
  if (!role || !roles.includes(role)) throw new Error('Your account is not assigned to this portal role. Contact your administrator.');
  const permissions = (Object.keys(CAPABILITIES) as Permission[]).filter(key => profile.permissions.includes(CAPABILITIES[key]!));
  const session = readSession();
  if (!session) throw new Error('Session ended. Please sign in again.');
  return {
    user: { id: profile.id, name: profile.username, email: profile.username.includes('@') ? profile.username : '',
      role, permissions, backendRoles: profile.roles, backendPermissions: profile.permissions, scopeMode: profile.scope_mode,
      facilityIds: profile.facility_ids, districtIds: profile.district_ids,
      facilityId: profile.facility_ids.length === 1 ? profile.facility_ids[0] : undefined },
    role, permissions, accessToken: session.accessToken, expiresIn: Math.max(0, (session.expiresAt - Date.now()) / 1000),
  };
}
export const authService = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const attempt = ++revision;
    clearSession();
    try {
      const body = new URLSearchParams({ username: credentials.email.trim(), password: credentials.password, grant_type: 'password' });
      if (credentials.mfaProof) body.set('mfa_proof', credentials.mfaProof);
      const tokens = await publicRequest<TokenPair>('/api/v1/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body,
      });
      if (attempt !== revision) throw new Error('Sign-in cancelled.');
      saveTokens(tokens, credentials.rememberMe === true);
      const identity = await currentIdentity(credentials.role);
      if (attempt !== revision) throw new Error('Sign-in cancelled.');
      return identity;
    } catch (error) { if (attempt === revision) clearSession(); throw error; }
  },
  async restoreSession(): Promise<AuthResponse | null> {
    if (restoring) return restoring;
    if (!readSession()) { clearSession(); return null; }
    const attempt = revision;
    restoring = currentIdentity().then(identity => attempt === revision ? identity : null)
      .catch(error => { if (attempt === revision) clearSession(); throw error; })
      .finally(() => { restoring = null; });
    return restoring;
  },
  async logout(): Promise<void> {
    revision++;
    try { if (readSession()) await apiRequest('/api/v1/auth/logout', { method: 'POST' }); }
    finally { clearSession(); }
  },
  async requestPasswordReset(username: string): Promise<void> {
    await publicRequest('/api/v1/auth/password/reset/request', { method: 'POST',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username }) });
  },
  getStoredSession: readSession,
  clearStoredSession: clearSession,
};
