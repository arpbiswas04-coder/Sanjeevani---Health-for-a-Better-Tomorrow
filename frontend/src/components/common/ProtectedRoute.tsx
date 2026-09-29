import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useUIStore, UserRole } from '@/store/uiStore';
import { ShieldAlert } from 'lucide-react';

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  redirectPath?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  allowedRoles,
  redirectPath = '/login',
}) => {
  // Mock auth state until Member 2 endpoints arrive; default to authenticated
  const isAuthenticated = true;
  const { activeRole } = useUIStore();

  if (!isAuthenticated) {
    return <Navigate to={redirectPath} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(activeRole)) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 mb-3">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-base font-bold text-slate-100">Access Restricted</h3>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Your current simulated role (<span className="font-semibold text-slate-200">{activeRole}</span>) does not have authorization for this command view.
        </p>
      </div>
    );
  }

  return <Outlet />;
};
