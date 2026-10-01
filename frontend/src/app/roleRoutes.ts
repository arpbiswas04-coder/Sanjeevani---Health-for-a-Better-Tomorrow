import { Role } from '@/types/auth';

export const ROLE_HOME: Record<Role, string> = {
  SUPER_ADMIN: '/admin/dashboard',
  NATIONAL_ADMIN: '/national/dashboard',
  STATE_ADMIN: '/state/dashboard',
  DISTRICT_ADMIN: '/district/dashboard',
  FACILITY_ADMIN: '/facility/dashboard',
};

export const getRoleHomeRoute = (role?: Role | null): string => {
  if (!role || !(role in ROLE_HOME)) {
    return '/login';
  }
  return ROLE_HOME[role];
};
