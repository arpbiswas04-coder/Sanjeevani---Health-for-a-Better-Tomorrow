import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/layouts/AppShell';
import { HomePage } from '@/pages/HomePage';
import { PlaceholderPage } from '@/pages/PlaceholderPage';

export const router = createBrowserRouter([
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
        element: (
          <PlaceholderPage
            title="Interactive Health Resource Map"
            phase="Phase 4 Roadmap"
            description="Geospatial visualization of primary health centers, cold-chain warehouses, and risk clusters using Leaflet/Mapbox GL."
          />
        ),
      },
      {
        path: 'facilities',
        element: (
          <PlaceholderPage
            title="Facilities & Hospitals Management"
            phase="Phase 3 Roadmap"
            description="Operational telemetry, tier level (PHC/CHC/DH), and facility profile management."
          />
        ),
      },
      {
        path: 'inventory',
        element: (
          <PlaceholderPage
            title="Real-Time Stock Monitoring"
            phase="Phase 5 Roadmap"
            description="Live stock ledger, batch tracking, barcode scanning, and inter-facility stock transfers."
          />
        ),
      },
      {
        path: 'expiry',
        element: (
          <PlaceholderPage
            title="Drug Expiry Tracking & Wastage"
            phase="Phase 5 Roadmap"
            description="Early warning risk queue for expiring pharmaceutical batches with automated redistribution suggestions."
          />
        ),
      },
      {
        path: 'beds',
        element: (
          <PlaceholderPage
            title="Bed Availability & Telemetry"
            phase="Phase 6 Roadmap"
            description="Real-time occupancy tracking for ICU, ventilator, oxygen, and general wards."
          />
        ),
      },
      {
        path: 'workforce',
        element: (
          <PlaceholderPage
            title="Workforce & Personnel Management"
            phase="Phase 6 Roadmap"
            description="Duty rosters, doctor-to-patient ratio monitoring, and attendance telemetry."
          />
        ),
      },
      {
        path: 'patients',
        element: (
          <PlaceholderPage
            title="Patient Footfall & Queue Telemetry"
            phase="Phase 6 Roadmap"
            description="OPD/IPD influx monitoring and triage bottleneck detection."
          />
        ),
      },
      {
        path: 'disease',
        element: (
          <PlaceholderPage
            title="Disease Trend Surveillance"
            phase="Phase 6 Roadmap"
            description="Epidemic outbreak detection and spatial disease cluster alerts."
          />
        ),
      },
      {
        path: 'emergency',
        element: (
          <PlaceholderPage
            title="Emergency Command Mode"
            phase="Phase 8 Roadmap"
            description="Crisis escalation dashboard, rapid resource mobilization, and disaster scenario simulations."
          />
        ),
      },
      {
        path: 'federated-ai',
        element: (
          <PlaceholderPage
            title="Federated AI Network Monitor"
            phase="Phase 9 Roadmap"
            description="Real-time status of edge hospital nodes, training rounds, differential privacy budgets, and model accuracy."
          />
        ),
      },
      {
        path: 'analytics',
        element: (
          <PlaceholderPage
            title="Healthcare Analytics & Resilience"
            phase="Phase 3 / 7 Roadmap"
            description="Historical trends, cost optimization, supply chain resilience score, and district benchmarking."
          />
        ),
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
