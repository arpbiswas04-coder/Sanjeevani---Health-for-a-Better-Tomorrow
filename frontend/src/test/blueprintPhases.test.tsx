import React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '@/modules/auth/LoginPage';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { EmergencyPage } from '@/modules/emergency/EmergencyPage';
import { AlertsPage } from '@/modules/alerts/AlertsPage';
import { useUIStore } from '@/store/uiStore';
import { offlineStorage } from '@/utils/offlineStorage';

// Helper wrapper with router
const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('Member 1 Blueprint — Phase & Critical Flow Verification', () => {
  beforeEach(() => {
    // Reset global Zustand store
    useUIStore.setState({
      activeRole: 'national_officer',
      toasts: [],
      isSidebarCollapsed: false,
    });
    offlineStorage.clearQueue();
  });

  // 1. Authentication & Role Presets
  describe('Phase 2 — Authentication & Role Presets', () => {
    it('renders login credentials form and prefilled role credentials', () => {
      renderWithRouter(<LoginPage />);

      expect(screen.getByText(/Authorized Personnel Single Sign-On/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Continue to MFA Verification/i })).toBeInTheDocument();

      // Click role preset button (e.g. District Collector / CMO)
      const roleBtn = screen.getByRole('button', { name: /District Collector \/ CMO/i });
      fireEvent.click(roleBtn);

      const emailInput = screen.getByDisplayValue(/cmo.lucknow@sanjeevani.gov.in/i) as HTMLInputElement;
      expect(emailInput).toBeInTheDocument();
    });

    it('triggers MFA challenge step upon credential submission', () => {
      renderWithRouter(<LoginPage />);

      const submitBtn = screen.getByRole('button', { name: /Continue to MFA Verification/i });
      fireEvent.click(submitBtn);

      expect(screen.getByText(/Enter Security Token/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/123456/i)).toBeInTheDocument();
    });
  });

  // 2. Phase 5 — Inventory UI
  describe('Phase 5 — Inventory & Stock Monitoring', () => {
    it('renders real-time medicine inventory table and stock items', () => {
      renderWithRouter(<InventoryPage />);

      expect(screen.getByText(/Real-Time Stock Monitoring & Batch Tracking/i)).toBeInTheDocument();
      expect(screen.getByText(/Paracetamol IV Infusion/i)).toBeInTheDocument();
      expect(screen.getByText(/Ceftriaxone Injection/i)).toBeInTheDocument();
      expect(screen.getByText(/Insulin Human Regular/i)).toBeInTheDocument();
    });

    it('filters inventory when typing into search input', () => {
      renderWithRouter(<InventoryPage />);

      const searchInput = screen.getByPlaceholderText(/Search by drug name, batch #, or facility.../i);
      fireEvent.change(searchInput, { target: { value: 'Insulin' } });

      expect(screen.getByText(/Insulin Human Regular/i)).toBeInTheDocument();
      expect(screen.queryByText(/Paracetamol 500mg/i)).not.toBeInTheDocument();
    });

    it('opens inter-facility redistribution transfer modal on click', () => {
      renderWithRouter(<InventoryPage />);

      const transferBtns = screen.getAllByRole('button', { name: /Transfer/i });
      fireEvent.click(transferBtns[0]);

      expect(screen.getByText(/Inter-Facility Stock Redistribution/i)).toBeInTheDocument();
    });
  });

  // 3. Phase 8 — Emergency Command UI
  describe('Phase 8 — Emergency Command Mode & What-If Simulation', () => {
    it('renders Emergency Command center and DEFCON readiness status', () => {
      renderWithRouter(<EmergencyPage />);

      expect(screen.getByText(/Emergency Command & Crisis Mobilization/i)).toBeInTheDocument();
      expect(screen.getByText(/DEFCON-1 Active/i)).toBeInTheDocument();
      expect(screen.getByText(/Vulnerability Deficit Priority Matrix/i)).toBeInTheDocument();
    });

    it('toggles emergency override protocol button', () => {
      renderWithRouter(<EmergencyPage />);

      const toggleBtn = screen.getByRole('button', { name: /DISENGAGE CRISIS/i });
      fireEvent.click(toggleBtn);

      expect(screen.getByRole('button', { name: /ACTIVATE CRISIS MODE/i })).toBeInTheDocument();
    });

    it('allows parameter adjustments in What-If crisis simulation scenario', () => {
      renderWithRouter(<EmergencyPage />);

      expect(screen.getByText(/Scenario Simulation Engine/i)).toBeInTheDocument();
      const runSimBtn = screen.getByRole('button', { name: /Compute Resilience Impact/i });
      expect(runSimBtn).toBeInTheDocument();
      fireEvent.click(runSimBtn);

      expect(screen.getByText(/Solving Constraint Matrices.../i)).toBeInTheDocument();
    });
  });

  // 4. Feature 58 — Alert Management UI
  describe('Feature 58 — Alert Management & Threshold Rules', () => {
    it('renders incident feed and allows incident acknowledgment', () => {
      renderWithRouter(<AlertsPage />);

      expect(screen.getByText(/Emergency Alert Management & Threshold Rules/i)).toBeInTheDocument();
      expect(screen.getByText(/Severe Insulin Stock-out Horizon/i)).toBeInTheDocument();

      const ackButtons = screen.getAllByRole('button', { name: /Acknowledge/i });
      expect(ackButtons.length).toBeGreaterThan(0);
      fireEvent.click(ackButtons[0]);

      expect(screen.getAllByText(/Acknowledged/i).length).toBeGreaterThan(0);
    });

    it('switches to threshold rules engine tab and displays active rules', () => {
      renderWithRouter(<AlertsPage />);

      const rulesTab = screen.getByRole('button', { name: /Threshold Engine/i });
      fireEvent.click(rulesTab);

      expect(screen.getByText(/Automated Alert Triggers & Early Warning Rules/i)).toBeInTheDocument();
      expect(screen.getByText(/Medicine Days-of-Inventory \(DOI\)/i)).toBeInTheDocument();
      expect(screen.getByText(/ICU Bed Occupancy Rate/i)).toBeInTheDocument();
    });
  });

  // 5. Offline Storage & PWA Telemetry Queue
  describe('PWA & Offline Telemetry Queue', () => {
    it('enqueues telemetry mutations into local offline storage when offline', () => {
      offlineStorage.enqueue({
        endpoint: '/api/v1/telemetry/beds',
        method: 'POST',
        payload: { facility_id: 'FAC-01', available_beds: 12 },
      });

      const queue = offlineStorage.getQueue();
      expect(queue.length).toBe(1);
      expect(queue[0].payload.facility_id).toBe('FAC-01');

      offlineStorage.clearQueue();
      expect(offlineStorage.getQueue().length).toBe(0);
    });
  });
});
