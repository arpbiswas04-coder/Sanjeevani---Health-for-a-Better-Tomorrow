import { User } from '@/types/auth';

// Route visibility mirrors backend capabilities. The API remains the security boundary.
const requirements: Record<string, string | null> = {
  dashboard: 'reports.read', map: 'inventory.read', states: 'reports.read', districts: 'reports.read',
  'district-comparison': 'reports.read', facilities: 'inventory.read', profile: null,
  inventory: 'inventory.read', stock: 'inventory.read', expiry: 'inventory.read', warehouses: 'procurement.read',
  beds: 'beds.read', workforce: 'workforce.read', attendance: 'workforce.read',
  patients: 'integration.read', disease: 'integration.read', equipment: 'equipment.read', ambulance: 'equipment.read',
  emergency: 'emergency.activate', alerts: 'alerts.read', analytics: 'reports.read', forecasting: 'reports.read',
  'federated-ai': 'federation.manage', users: 'admin.users', roles: 'admin.users',
  config: 'admin.config', settings: 'admin.config', monitoring: 'admin.config', 'audit-logs': 'audit.read',
};
export function canAccessPath(path: string, user: User | null): boolean {
  if (!user) return false;
  const parts = path.split('/').filter(Boolean);
  const screen = parts.length === 1 && ['admin', 'national', 'state', 'district', 'facility'].includes(parts[0])
    ? 'dashboard' : parts[parts.length - 1] || 'dashboard';
  if (parts[0] === 'admin' && user.scopeMode !== 'global') return false;
  const required = parts[0] === 'admin' && screen === 'dashboard' ? 'admin.users' : requirements[screen];
  if (required === undefined) return false;
  if (screen === 'warehouses') return !!user.backendPermissions?.some(p => p === 'inventory.read' || p === 'procurement.read');
  return required === null || !!user.backendPermissions?.includes(required);
}
