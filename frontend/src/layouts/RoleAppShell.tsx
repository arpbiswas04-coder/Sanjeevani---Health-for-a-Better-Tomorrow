import React from 'react';
import { Outlet } from 'react-router-dom';
import { RoleSidebar } from '@/components/common/RoleSidebar';
import { RoleTopBar } from '@/components/common/RoleTopBar';
import { OfflineIndicator } from '@/components/common/OfflineIndicator';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { CommandPalette } from '@/components/common/CommandPalette';
import { useUIStore } from '@/store/uiStore';

export const RoleAppShell: React.FC = () => {
  const { isSidebarCollapsed } = useUIStore();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Offline Connectivity Notification */}
      <OfflineIndicator />

      {/* Role Navigation Sidebar */}
      <RoleSidebar />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          isSidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        } pb-16 lg:pb-0`}
      >
        <RoleTopBar />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto animate-in fade-in duration-200">
          <Outlet />
        </main>

        <footer className="border-t border-slate-800/60 py-4 px-6 text-center text-xs text-slate-500">
          Sanjeevani Grid • Federated AI-Powered Smart Health & Supply Chain Resilience Platform
        </footer>
      </div>

      {/* Global Feedback Systems */}
      <ToastContainer />
      <CommandPalette />
    </div>
  );
};

export default RoleAppShell;
