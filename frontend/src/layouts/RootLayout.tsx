import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from '@/components/common/Header';

export const RootLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Header />
      <main className="flex-1 container mx-auto px-6 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500">
        Sanjeevani Grid © 2026 • Federated AI-powered Smart Health & Supply Chain Resilience Platform
      </footer>
    </div>
  );
};
