import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { HomePage } from '@/pages/HomePage';
import { RegionalDashboard } from '@/modules/dashboard/RegionalDashboard';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { PatientsPage } from '@/modules/patients/PatientsPage';
import { DiseasePage } from '@/modules/disease/DiseasePage';
import { EquipmentPage } from '@/modules/equipment/EquipmentPage';
import { EmergencyPage } from '@/modules/emergency/EmergencyPage';
import { FederatedAIPage } from '@/modules/federated-ai/FederatedAIPage';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { AdminPage } from '@/modules/admin/AdminPage';
import { LoginPage } from '@/modules/auth/LoginPage';
import { RegisterPage } from '@/modules/auth/RegisterPage';
import { ProfilePage } from '@/modules/auth/ProfilePage';
import { SettingsPage } from '@/modules/auth/SettingsPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'dashboard/regional',
        element: <RegionalDashboard />,
      },
      {
        path: 'map',
        element: <InteractiveResourceMap />,
      },
      {
        path: 'facilities',
        element: <FacilitiesPage />,
      },
      {
        path: 'inventory',
        element: <InventoryPage />,
      },
      {
        path: 'expiry',
        element: <InventoryPage />,
      },
      {
        path: 'beds',
        element: <BedsPage />,
      },
      {
        path: 'workforce',
        element: <WorkforcePage />,
      },
      {
        path: 'patients',
        element: <PatientsPage />,
      },
      {
        path: 'disease',
        element: <DiseasePage />,
      },
      {
        path: 'equipment',
        element: <EquipmentPage />,
      },
      {
        path: 'emergency',
        element: <EmergencyPage />,
      },
      {
        path: 'federated-ai',
        element: <FederatedAIPage />,
      },
      {
        path: 'alerts',
        element: <AlertsPage />,
      },
      {
        path: 'analytics',
        element: <AIDashboard />,
      },
      {
        path: 'admin',
        element: <AdminPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
]);
