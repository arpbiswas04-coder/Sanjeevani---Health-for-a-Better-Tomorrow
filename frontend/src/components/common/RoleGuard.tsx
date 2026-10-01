import React, { useEffect } from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Role } from '@/types/auth';
import { LoadingScreen } from '@/components/ui/LoadingScreen';

interface RoleGuardProps {
  allowedRoles?: Role[];
  children?: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { isAuthenticated, role, isRestoring, restoreSession } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (isRestoring) {
      restoreSession();
    }
  }, [isRestoring, restoreSession]);

  if (isRestoring) {
    return <LoadingScreen message="Verifying security credentials and restoring session..." />;
  }

  if (!isAuthenticated || !role) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(role)) {
    return <Navigate to="/unauthorized" state={{ attemptedUrl: location.pathname, currentRole: role }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default RoleGuard;
