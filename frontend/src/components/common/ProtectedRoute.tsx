import React from 'react';
import { RoleGuard } from './RoleGuard';
import { UserRole } from '@/store/uiStore';
import { Role } from '@/types/auth';

const LEGACY_ROLES: Partial<Record<UserRole, Role>> = {
  national_officer: 'NATIONAL_ADMIN', state_officer: 'STATE_ADMIN',
  district_officer: 'DISTRICT_ADMIN', facility_admin: 'FACILITY_ADMIN',
};
export const ProtectedRoute: React.FC<{ allowedRoles?: UserRole[]; redirectPath?: string }> = ({ allowedRoles }) => {
  // Legacy callers use the same verified session; simulated UI roles are never credentials.
  const mapped = allowedRoles?.map(role => LEGACY_ROLES[role]).filter((role): role is Role => !!role);
  if (allowedRoles?.length && !mapped?.length) return <div role="alert">Access Restricted</div>;
  return <RoleGuard allowedRoles={mapped} />;
};
