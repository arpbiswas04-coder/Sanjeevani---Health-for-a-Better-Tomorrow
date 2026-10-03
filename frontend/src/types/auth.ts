// Role and Authorization Types for Sanjeevani Grid

export type Role =
  | 'SUPER_ADMIN'
  | 'NATIONAL_ADMIN'
  | 'STATE_ADMIN'
  | 'DISTRICT_ADMIN'
  | 'FACILITY_ADMIN';

export const ROLE_LABELS: Record<Role, string> = {
  SUPER_ADMIN: 'System Administrator',
  NATIONAL_ADMIN: 'National Health Command',
  STATE_ADMIN: 'State Health Authority',
  DISTRICT_ADMIN: 'District Health Authority',
  FACILITY_ADMIN: 'Hospital / PHC Administrator',
};

export type Permission =
  | 'dashboard:view'
  | 'facility:view'
  | 'inventory:view'
  | 'inventory:update'
  | 'beds:view'
  | 'beds:update'
  | 'workforce:view'
  | 'analytics:view'
  | 'alerts:view'
  | 'emergency:view'
  | 'emergency:override'
  | 'federated:manage'
  | 'users:manage'
  | 'roles:manage'
  | 'system:config';

export interface User {
  backendRoles?: string[];
  backendPermissions?: string[];
  scopeMode?: string;
  facilityIds?: string[];
  districtIds?: string[];
  id: string;
  name: string;
  email: string;
  role: Role;
  permissions: Permission[];
  state?: string;
  district?: string;
  facilityId?: string;
  facilityName?: string;
  designation?: string;
  phone?: string;
  avatarUrl?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  role?: Role;
  mfaProof?: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  user: User;
  role: Role;
  permissions: Permission[];
  accessToken: string;
  expiresIn: number;
}

export interface DashboardScope {
  level: 'national' | 'state' | 'district' | 'facility' | 'system';
  state?: string;
  district?: string;
  facilityId?: string;
  facilityName?: string;
}
