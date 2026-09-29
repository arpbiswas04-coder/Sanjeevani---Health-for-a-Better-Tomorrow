import { LoginRequest, AuthResponse, User, Role, Permission } from '@/types/auth';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const STORAGE_KEY = 'sanjeevani_auth_session';

// Standard provisioned accounts representing the 5 authoritative role tiers
export const DEMO_ACCOUNTS: Record<Role, { email: string; pass: string; user: User }> = {
  SUPER_ADMIN: {
    email: 'admin.system@sanjeevani.gov.in',
    pass: 'SuperSecure2026!',
    user: {
      id: 'USR-SUPER-01',
      name: 'Vikramaditya Sharma',
      email: 'admin.system@sanjeevani.gov.in',
      role: 'SUPER_ADMIN',
      designation: 'Principal System Architect & Administrator',
      permissions: [
        'dashboard:view',
        'facility:view',
        'inventory:view',
        'inventory:update',
        'beds:view',
        'beds:update',
        'workforce:view',
        'analytics:view',
        'alerts:view',
        'emergency:view',
        'emergency:override',
        'federated:manage',
        'users:manage',
        'roles:manage',
        'system:config',
      ],
    },
  },
  NATIONAL_ADMIN: {
    email: 'national.command@sanjeevani.gov.in',
    pass: 'NationalPass2026!',
    user: {
      id: 'USR-NAT-01',
      name: 'Dr. Aarav Patel',
      email: 'national.command@sanjeevani.gov.in',
      role: 'NATIONAL_ADMIN',
      designation: 'National Director, Health Surveillance Command',
      permissions: [
        'dashboard:view',
        'facility:view',
        'inventory:view',
        'inventory:update',
        'beds:view',
        'beds:update',
        'workforce:view',
        'analytics:view',
        'alerts:view',
        'emergency:view',
        'emergency:override',
        'federated:manage',
      ],
    },
  },
  STATE_ADMIN: {
    email: 'state.up@sanjeevani.gov.in',
    pass: 'StatePass2026!',
    user: {
      id: 'USR-ST-UP-01',
      name: 'Dr. Sunita Rao',
      email: 'state.up@sanjeevani.gov.in',
      role: 'STATE_ADMIN',
      state: 'Uttar Pradesh',
      designation: 'State Health Commissioner, Uttar Pradesh',
      permissions: [
        'dashboard:view',
        'facility:view',
        'inventory:view',
        'inventory:update',
        'beds:view',
        'beds:update',
        'workforce:view',
        'analytics:view',
        'alerts:view',
        'emergency:view',
      ],
    },
  },
  DISTRICT_ADMIN: {
    email: 'district.lucknow@sanjeevani.gov.in',
    pass: 'DistrictPass2026!',
    user: {
      id: 'USR-DIST-LKO-01',
      name: 'Rajesh K. Verma, IAS',
      email: 'district.lucknow@sanjeevani.gov.in',
      role: 'DISTRICT_ADMIN',
      state: 'Uttar Pradesh',
      district: 'Lucknow',
      designation: 'District Magistrate & Chief Health Officer, Lucknow',
      permissions: [
        'dashboard:view',
        'facility:view',
        'inventory:view',
        'inventory:update',
        'beds:view',
        'workforce:view',
        'analytics:view',
        'alerts:view',
        'emergency:view',
      ],
    },
  },
  FACILITY_ADMIN: {
    email: 'facility.rml@sanjeevani.gov.in',
    pass: 'FacilityPass2026!',
    user: {
      id: 'USR-FAC-RML-01',
      name: 'Dr. Ananya Sen',
      email: 'facility.rml@sanjeevani.gov.in',
      role: 'FACILITY_ADMIN',
      state: 'Uttar Pradesh',
      district: 'Lucknow',
      facilityId: 'fac-002',
      facilityName: 'Dr. RML Hospital, Lucknow',
      designation: 'Medical Superintendent, Dr. RML Hospital',
      permissions: [
        'dashboard:view',
        'facility:view',
        'inventory:view',
        'inventory:update',
        'beds:view',
        'beds:update',
        'workforce:view',
        'alerts:view',
      ],
    },
  },
};

export const authService = {
  /**
   * Login with email, password, and selected role.
   * Authoritative role check: user.role must match selected role.
   */
  async login(request: LoginRequest): Promise<AuthResponse> {
    const { email, password, role: selectedRole } = request;

    // First attempt to call backend auth endpoint if available
    try {
      const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role: selectedRole }),
      });

      if (response.ok) {
        const data: AuthResponse = await response.json();
        // Server validation check
        if (data.user.role !== selectedRole) {
          throw new Error('The selected role does not match this account.');
        }
        this.storeSession(data);
        return data;
      }
    } catch (err: unknown) {
      // If error is our own role mismatch error, propagate it!
      if (err instanceof Error && err.message === 'The selected role does not match this account.') {
        throw err;
      }
      // Otherwise proceed to fallback demo credential verification
    }

    // Fallback credential lookup across authoritative accounts
    const accountEntry = Object.values(DEMO_ACCOUNTS).find(
      (acc) => acc.email.toLowerCase() === email.trim().toLowerCase()
    );

    if (!accountEntry) {
      throw new Error('Invalid credentials. Please verify your credentials or select a demo account below.');
    }

    // Validate selected role against authoritative account role first if account found
    if (accountEntry.user.role !== selectedRole) {
      throw new Error('The selected role does not match this account.');
    }

    // Verify password
    if (accountEntry.pass !== password) {
      throw new Error('Invalid credentials. Please verify your credentials or select a demo account below.');
    }

    // Build authoritative auth response
    const authResponse: AuthResponse = {
      user: accountEntry.user,
      role: accountEntry.user.role,
      permissions: accountEntry.user.permissions,
      accessToken: `sg_jwt_${accountEntry.user.role.toLowerCase()}_${Date.now()}`,
      expiresIn: 86400,
    };

    this.storeSession(authResponse);
    return authResponse;
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.getStoredSession()?.accessToken || ''}`,
        },
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      this.clearStoredSession();
    }
  },

  storeSession(session: AuthResponse): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
  },

  getStoredSession(): AuthResponse | null {
    if (typeof window === 'undefined') return null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as AuthResponse;
    } catch {
      return null;
    }
  },

  clearStoredSession(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  },
};
