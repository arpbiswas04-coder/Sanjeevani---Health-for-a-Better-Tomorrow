import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './router';
import { useAuthStore } from '@/store/authStore';
import '@/i18n';
import { SESSION_EVENT, readSession } from '@/services/httpClient';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  const { restoreSession } = useAuthStore();

  useEffect(() => {
    restoreSession();
    const clearCache = () => { if (!readSession()) { void queryClient.cancelQueries(); queryClient.clear(); } };
    const verify = () => { if (readSession()) void restoreSession(); };
    window.addEventListener(SESSION_EVENT, clearCache);
    window.addEventListener('focus', verify);
    const storageChanged = () => { void queryClient.cancelQueries(); queryClient.clear(); void restoreSession(); };
    window.addEventListener('storage', storageChanged);
    return () => {
      window.removeEventListener(SESSION_EVENT, clearCache); window.removeEventListener('focus', verify);
      window.removeEventListener('storage', storageChanged);
    };
  }, [restoreSession]);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};

export default App;
