import { create } from 'zustand';

interface AppState {
  theme: 'dark' | 'light';
  isSidebarOpen: boolean;
  setTheme: (theme: 'dark' | 'light') => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'dark',
  isSidebarOpen: true,
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
}));
