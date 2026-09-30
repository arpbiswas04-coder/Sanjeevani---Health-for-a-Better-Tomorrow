import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { getRoleHomeRoute } from '@/app/roleRoutes';

// Layouts
import { RoleAppShell } from '@/layouts/RoleAppShell';
import { AdminLayout } from '@/layouts/AdminLayout';
import { NationalLayout } from '@/layouts/NationalLayout';
import { StateLayout } from '@/layouts/StateLayout';
import { DistrictLayout } from '@/layouts/DistrictLayout';
import { FacilityLayout } from '@/layouts/FacilityLayout';

// Guards & Fallbacks
import { RoleGuard } from '@/components/common/RoleGuard';
import { UnauthorizedPage } from '@/pages/UnauthorizedPage';

// Auth Pages
import { LoginPage } from '@/modules/auth/LoginPage';
import { RegisterPage } from '@/modules/auth/RegisterPage';
import { MFAPage } from '@/modules/auth/MFAPage';
import { ForgotPasswordPage } from '@/modules/auth/ForgotPasswordPage';
import { ProfilePage } from '@/modules/auth/ProfilePage';
import { SettingsPage } from '@/modules/auth/SettingsPage';

// Dashboards
import { NationalDashboardPage } from '@/modules/dashboard/NationalDashboardPage';
import { StateDashboardPage } from '@/modules/dashboard/StateDashboardPage';
import { DistrictDashboardPage } from '@/modules/dashboard/DistrictDashboardPage';
import { FacilityDashboardPage } from '@/modules/dashboard/FacilityDashboardPage';
import { SuperAdminDashboardPage } from '@/modules/dashboard/SuperAdminDashboardPage';
import { RegionalDashboard } from '@/modules/dashboard/RegionalDashboard';

// Module Views
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { PatientsPage } from '@/modules/patients/PatientsPage';
import { DiseasePage } from '@/modules/disease/DiseasePage';
import { EquipmentPage } from '@/modules/equipment/EquipmentPage';
import { EmergencyPage } from '@/modules/emergency/EmergencyPage';
import { FederatedAIPage } from '@/modules/federated-ai/FederatedAIPage';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { AdminPage } from '@/modules/admin/AdminPage';

// Root Index Redirector based on session
const RootRedirect: React.FC = () => {
  const { isAuthenticated, role } = useAuthStore();
  if (isAuthenticated && role) {
    return <Navigate to={getRoleHomeRoute(role)} replace />;
  }
  return <Navigate to="/login" replace />;
};

export const router = createBrowserRouter([
  // Public Auth Routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/mfa',
    element: <MFAPage />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },

  // Index Route (Redirects to role home or /login)
  {
    path: '/',
    element: <RootRedirect />,
  },

  // 1. SUPER_ADMIN Protected Routes (/admin/*)
  {
    path: '/admin',
    element: (
      <RoleGuard allowedRoles={['SUPER_ADMIN']}>
        <AdminLayout />
      </RoleGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/admin/dashboard" replace /> },
      { path: 'dashboard', element: <SuperAdminDashboardPage /> },
      { path: 'users', element: <AdminPage /> },
      { path: 'roles', element: <AdminPage /> },
      { path: 'config', element: <SettingsPage /> },
      { path: 'facilities', element: <FacilitiesPage /> },
      { path: 'monitoring', element: <AdminPage /> },
      { path: 'audit-logs', element: <AdminPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },

  // 2. NATIONAL_ADMIN Protected Routes (/national/*)
  {
    path: '/national',
    element: (
      <RoleGuard allowedRoles={['NATIONAL_ADMIN', 'SUPER_ADMIN']}>
        <NationalLayout />
      </RoleGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/national/dashboard" replace /> },
      { path: 'dashboard', element: <NationalDashboardPage /> },
      { path: 'map', element: <InteractiveResourceMap /> },
      { path: 'states', element: <RegionalDashboard /> },
      { path: 'district-comparison', element: <RegionalDashboard /> },
      { path: 'facilities', element: <FacilitiesPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'warehouses', element: <WarehouseDashboardPage /> },
      { path: 'beds', element: <BedsPage /> },
      { path: 'workforce', element: <WorkforcePage /> },
      { path: 'patients', element: <PatientsPage /> },
      { path: 'disease', element: <DiseasePage /> },
      { path: 'emergency', element: <EmergencyPage /> },
      { path: 'forecasting', element: <AIDashboard /> },
      { path: 'federated-ai', element: <FederatedAIPage /> },
      { path: 'analytics', element: <AIDashboard /> },
      { path: 'alerts', element: <AlertsPage /> },
    ],
  },

  // 3. STATE_ADMIN Protected Routes (/state/*)
  {
    path: '/state',
    element: (
      <RoleGuard allowedRoles={['STATE_ADMIN', 'NATIONAL_ADMIN', 'SUPER_ADMIN']}>
        <StateLayout />
      </RoleGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/state/dashboard" replace /> },
      { path: 'dashboard', element: <StateDashboardPage /> },
      { path: 'map', element: <InteractiveResourceMap /> },
      { path: 'districts', element: <RegionalDashboard /> },
      { path: 'facilities', element: <FacilitiesPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'beds', element: <BedsPage /> },
      { path: 'workforce', element: <WorkforcePage /> },
      { path: 'patients', element: <PatientsPage /> },
      { path: 'disease', element: <DiseasePage /> },
      { path: 'emergency', element: <EmergencyPage /> },
      { path: 'analytics', element: <AIDashboard /> },
      { path: 'alerts', element: <AlertsPage /> },
    ],
  },

  // 4. DISTRICT_ADMIN Protected Routes (/district/*)
  {
    path: '/district',
    element: (
      <RoleGuard allowedRoles={['DISTRICT_ADMIN', 'STATE_ADMIN', 'NATIONAL_ADMIN', 'SUPER_ADMIN']}>
        <DistrictLayout />
      </RoleGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/district/dashboard" replace /> },
      { path: 'dashboard', element: <DistrictDashboardPage /> },
      { path: 'map', element: <InteractiveResourceMap /> },
      { path: 'facilities', element: <FacilitiesPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'beds', element: <BedsPage /> },
      { path: 'workforce', element: <WorkforcePage /> },
      { path: 'patients', element: <PatientsPage /> },
      { path: 'disease', element: <DiseasePage /> },
      { path: 'emergency', element: <EmergencyPage /> },
      { path: 'analytics', element: <AIDashboard /> },
      { path: 'alerts', element: <AlertsPage /> },
    ],
  },

  // 5. FACILITY_ADMIN Protected Routes (/facility/*)
  {
    path: '/facility',
    element: (
      <RoleGuard allowedRoles={['FACILITY_ADMIN', 'DISTRICT_ADMIN', 'STATE_ADMIN', 'NATIONAL_ADMIN', 'SUPER_ADMIN']}>
        <FacilityLayout />
      </RoleGuard>
    ),
    children: [
      { index: true, element: <Navigate to="/facility/dashboard" replace /> },
      { path: 'dashboard', element: <FacilityDashboardPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'stock', element: <InventoryPage /> },
      { path: 'expiry', element: <InventoryPage /> },
      { path: 'beds', element: <BedsPage /> },
      { path: 'workforce', element: <WorkforcePage /> },
      { path: 'attendance', element: <WorkforcePage /> },
      { path: 'patients', element: <PatientsPage /> },
      { path: 'equipment', element: <EquipmentPage /> },
      { path: 'ambulance', element: <EquipmentPage /> },
      { path: 'alerts', element: <AlertsPage /> },
      { path: 'profile', element: <ProfilePage /> },
    ],
  },

  // Common Protected Shell for Universal Tools & Backward Compatibility
  {
    element: (
      <RoleGuard>
        <RoleAppShell />
      </RoleGuard>
    ),
    children: [
      { path: 'map', element: <InteractiveResourceMap /> },
      { path: 'facilities', element: <FacilitiesPage /> },
      { path: 'warehouses', element: <WarehouseDashboardPage /> },
      { path: 'inventory', element: <InventoryPage /> },
      { path: 'expiry', element: <InventoryPage /> },
      { path: 'beds', element: <BedsPage /> },
      { path: 'workforce', element: <WorkforcePage /> },
      { path: 'patients', element: <PatientsPage /> },
      { path: 'disease', element: <DiseasePage /> },
      { path: 'equipment', element: <EquipmentPage /> },
      { path: 'emergency', element: <EmergencyPage /> },
      { path: 'federated-ai', element: <FederatedAIPage /> },
      { path: 'alerts', element: <AlertsPage /> },
      { path: 'analytics', element: <AIDashboard /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },

  // Fallback Catch-all
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export default router;
