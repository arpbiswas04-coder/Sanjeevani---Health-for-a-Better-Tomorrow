import { create } from 'zustand';
import { User, Role, Permission, LoginRequest } from '@/types/auth';
import { authService } from '@/services/authService';
import { getRoleHomeRoute } from '@/app/roleRoutes';

interface AuthState {
  user: User | null;
  role: Role | null;
  permissions: Permission[];
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isRestoring: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<string>;
  logout: () => Promise<void>;
  restoreSession: () => Promise<boolean>;
  clearError: () => void;
  hasPermission: (permission: Permission) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  role: null,
  permissions: [],
  accessToken: null,
  isAuthenticated: false,
  isLoading: false,
  isRestoring: true, // starts true on load until restoreSession finishes
  error: null,

  login: async (credentials: LoginRequest): Promise<string> => {
    set({ isLoading: true, error: null });
    try {
      const response = await authService.login(credentials);
      set({
        user: response.user,
        role: response.role,
        permissions: response.permissions,
        accessToken: response.accessToken,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return getRoleHomeRoute(response.role);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Authentication failed. Please check your network and credentials.';
      set({
        isLoading: false,
        isAuthenticated: false,
        user: null,
        role: null,
        permissions: [],
        accessToken: null,
        error: errorMessage,
      });
      throw err;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await authService.logout();
    } finally {
      set({
        user: null,
        role: null,
        permissions: [],
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  restoreSession: async (): Promise<boolean> => {
    set({ isRestoring: true });
    try {
      const session = authService.getStoredSession();
      if (session && session.accessToken && session.user && session.role) {
        set({
          user: session.user,
          role: session.role,
          permissions: session.permissions || [],
          accessToken: session.accessToken,
          isAuthenticated: true,
          isRestoring: false,
          error: null,
        });
        return true;
      }
      set({
        user: null,
        role: null,
        permissions: [],
        accessToken: null,
        isAuthenticated: false,
        isRestoring: false,
      });
      return false;
    } catch {
      set({
        user: null,
        role: null,
        permissions: [],
        accessToken: null,
        isAuthenticated: false,
        isRestoring: false,
      });
      return false;
    }
  },

  clearError: () => set({ error: null }),

  hasPermission: (permission: Permission): boolean => {
    const { permissions, role } = get();
    if (role === 'SUPER_ADMIN') return true;
    return permissions.includes(permission);
  },
}));
