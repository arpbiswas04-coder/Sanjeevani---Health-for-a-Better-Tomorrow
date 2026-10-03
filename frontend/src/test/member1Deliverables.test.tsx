import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

import { MFAPage } from '@/modules/auth/MFAPage';
import { ForgotPasswordPage } from '@/modules/auth/ForgotPasswordPage';
import { NationalDashboardPage } from '@/modules/dashboard/NationalDashboardPage';
import { WarehouseDashboardPage } from '@/modules/facilities/WarehouseDashboardPage';
import { InteractiveResourceMap } from '@/modules/map/InteractiveResourceMap';
import { WorkforcePage } from '@/modules/workforce/WorkforcePage';
import { FederatedAIPage } from '@/modules/federated-ai/FederatedAIPage';
import { AIDashboard } from '@/modules/analytics/AIDashboard';
import { InventoryPage } from '@/modules/inventory/InventoryPage';
import { offlineStorage } from '@/utils/offlineStorage';
import { LoginPage } from '@/modules/auth/LoginPage';

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('Member 1 Complete Blueprint Deliverables Verification', () => {
  afterEach(() => vi.unstubAllGlobals());
  beforeEach(() => {
    offlineStorage.clearQueue();
  });

  describe('Phase 2 — Multi-Factor Authentication & Account Recovery', () => {
    it('directs MFA verification to backend login instead of simulating success', () => {
      renderWithRouter(<MFAPage />);
      expect(screen.getByText(/Multi-factor authentication/i)).toBeInTheDocument();
      expect(screen.getByText(/backend must verify/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Return to sign in/i })).toHaveAttribute('href', '/login');
    });

    it('accepts optional MFA proof with credentials, without an emergency bypass', () => {
      renderWithRouter(<LoginPage />);
      const proof = screen.getByLabelText('MFA proof (if required)');
      fireEvent.change(proof, { target: { value: '123456' } });
      expect(proof).toHaveValue('123456');
      expect(screen.queryByRole('button', { name: /Verify Identity & Proceed/i })).toBeNull();
    });

    it('renders ForgotPasswordPage and handles submission', async () => {
      const request = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, data: { message: 'If eligible' } }), { status: 202 }));
      vi.stubGlobal('fetch', request);
      renderWithRouter(<ForgotPasswordPage />);
      expect(screen.getByText(/Account Recovery/i)).toBeInTheDocument();

      const emailInput = screen.getByLabelText('Username');
      fireEvent.change(emailInput, { target: { value: 'cmo@mohfw.gov.in' } });

      const submitBtn = screen.getByRole('button', { name: /Request recovery/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/If the account is eligible and delivery is configured/i)).toBeInTheDocument();
      });
      expect(request.mock.calls[0][0]).toMatch(/\/auth\/password\/reset\/request$/);
      expect(JSON.parse(request.mock.calls[0][1].body)).toEqual({ username: 'cmo@mohfw.gov.in' });
    });
  });

  // Data, map, operations and unsupported-feature assertions: dataIntegration.test.tsx.
});
