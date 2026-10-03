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
    it('renders empty credentials and never autofills demo accounts when selecting a role', () => {
      renderWithRouter(<LoginPage />);

      expect(screen.getByText(/Command Access Portal/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign In to Command Portal/i })).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'DISTRICT_ADMIN' } });
      expect(screen.getByLabelText('Official Email / Username')).toHaveValue('');
      expect(screen.getByLabelText('Passcode / Password')).toHaveValue('');
      expect(screen.queryByText(/Fast Role Demo Presets/)).not.toBeInTheDocument();
    });

    it('validates password visibility toggle', () => {
      renderWithRouter(<LoginPage />);

      const passInput = screen.getByLabelText(/Passcode/i) as HTMLInputElement;
      expect(passInput.type).toBe('password');

      const toggleBtn = screen.getByRole('button', { name: /Show password/i });
      fireEvent.click(toggleBtn);
      expect(passInput.type).toBe('text');
    });
  });

  // Operational integration coverage: dataIntegration.test.tsx; fabricated workflow assertions removed.

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
