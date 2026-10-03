import { create } from 'zustand';
import { User, Role, Permission, LoginRequest, AuthResponse } from '@/types/auth';
import { authService } from '@/services/authService';
import { readSession, SESSION_EVENT } from '@/services/httpClient';
import { getRoleHomeRoute } from '@/app/roleRoutes';
import { canAccessPath } from '@/app/authorization';

interface AuthState {
  user: User | null; role: Role | null; permissions: Permission[]; accessToken: string | null;
  isAuthenticated: boolean; isLoading: boolean; isRestoring: boolean; error: string | null;
  login: (credentials: LoginRequest) => Promise<string>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  clearError: () => void;
  hasPermission: (permission: Permission) => boolean;
}
const empty = { user: null, role: null, permissions: [], accessToken: null, isAuthenticated: false };
const authenticated = (response: AuthResponse) => ({ user: response.user, role: response.role,
  permissions: response.permissions, accessToken: response.accessToken, isAuthenticated: true });
let operation = 0;
let restoration: Promise<boolean> | null = null;
export const useAuthStore = create<AuthState>((set, get) => ({
  ...empty, isLoading: false, isRestoring: true, error: null,
  login: async credentials => {
    const attempt = ++operation;
    set({ ...empty, isLoading: true, isRestoring: false, error: null });
    try {
      const response = await authService.login(credentials);
      if (attempt !== operation) throw new Error('Sign-in cancelled.');
      set({ ...authenticated(response), isLoading: false });
      const home = getRoleHomeRoute(response.role);
      return canAccessPath(home, response.user) ? home : '/profile';
    } catch (error) {
      if (attempt === operation) set({ ...empty, isLoading: false, error: error instanceof Error ? error.message : 'Authentication failed.' });
      throw error;
    }
  },
  logout: async () => {
    ++operation;
    set({ isLoading: true });
    let error: string | null = null;
    try { await authService.logout(); }
    catch { error = 'Signed out on this terminal. The backend could not confirm session revocation; other sessions may remain active until expiry.'; }
    finally { set({ ...empty, isLoading: false, isRestoring: false, error }); }
  },
  restoreSession: () => {
    if (restoration) return restoration;
    const attempt = operation;
    set({ isRestoring: true });
    restoration = (async () => {
      try {
        const response = await authService.restoreSession();
        if (attempt !== operation) return false;
        set({ ...(response ? authenticated(response) : empty), isRestoring: false });
        return !!response;
      } catch (error) {
        if (attempt === operation) set({ ...empty, isRestoring: false, error: error instanceof Error ? error.message : 'Session verification failed.' });
        return false;
      } finally { restoration = null; }
    })();
    return restoration;
  },
  clearError: () => set({ error: null }),
  hasPermission: permission => get().isAuthenticated && get().permissions.includes(permission),
}));

window.addEventListener(SESSION_EVENT, () => {
  const session = readSession();
  if (!session) useAuthStore.setState(empty);
  else if (useAuthStore.getState().isAuthenticated) useAuthStore.setState({ accessToken: session.accessToken });
});
