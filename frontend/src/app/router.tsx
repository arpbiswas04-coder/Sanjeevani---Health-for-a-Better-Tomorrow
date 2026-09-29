import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { HomePage } from '@/pages/HomePage';
import { PlaceholderPage } from '@/pages/PlaceholderPage';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { BedsPage } from '@/modules/beds/BedsPage';
import { FacilitiesPage } from '@/modules/facilities/FacilitiesPage';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { DiseasePage } from '@/modules/disease/DiseasePage';
import { EmergencyPage } from '@/modules/emergency/EmergencyPage';
import { FederatedAIPage } from '@/modules/federated-ai/FederatedAIPage';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { LoginPage } from '@/modules/auth/LoginPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
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
        element: (
          <PlaceholderPage
            title="Patient Footfall & Queue Telemetry"
            phase="Phase 6 Roadmap"
            description="OPD/IPD influx monitoring, triage bottleneck detection, and patient wait time telemetry."
          />
        ),
      },
      {
        path: 'disease',
        element: <DiseasePage />,
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
        path: 'analytics',
        element: <AIDashboard />,
      },
      {
        path: 'settings',
        element: (
          <PlaceholderPage
            title="Platform Settings & Security"
            phase="Phase 1 Foundation"
            description="System configurations, role permissions, encryption keys, and edge node connectivity parameters."
          />
        ),
      },
    ],
  },
]);
