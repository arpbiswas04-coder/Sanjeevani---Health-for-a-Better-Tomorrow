import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
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

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('Member 1 Complete Blueprint Deliverables Verification', () => {
  beforeEach(() => {
    offlineStorage.clearQueue();
  });

  describe('Phase 2 — Multi-Factor Authentication & Account Recovery', () => {
    it('renders MFAPage with 6-digit TOTP input inputs', () => {
      renderWithRouter(<MFAPage />);
      expect(screen.getByText(/Two-Factor Verification/i)).toBeInTheDocument();
      expect(screen.getByText(/Enter 6-Digit Authenticator Code/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Verify Identity & Proceed/i })).toBeInTheDocument();
    });

    it('allows switching to emergency recovery key on MFAPage', () => {
      renderWithRouter(<MFAPage />);
      const backupBtn = screen.getByRole('button', { name: /Use emergency recovery key/i });
      fireEvent.click(backupBtn);

      expect(screen.getByText(/Emergency Recovery Key/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/e\.g\. SANJ-XXXX-XXXX-XXXX/i)).toBeInTheDocument();
    });

    it('renders ForgotPasswordPage and handles submission', async () => {
      renderWithRouter(<ForgotPasswordPage />);
      expect(screen.getByText(/Account Recovery/i)).toBeInTheDocument();

      const emailInput = screen.getByPlaceholderText(/officer@sanjeevani\.gov\.in/i);
      fireEvent.change(emailInput, { target: { value: 'cmo@mohfw.gov.in' } });

      const submitBtn = screen.getByRole('button', { name: /Send Password Reset Instructions/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/Recovery Instructions Dispatched/i)).toBeInTheDocument();
      });
    });
  });

  describe('Phase 3 — National Health Command Dashboard', () => {
    it('renders national KPIs, state resilience chart, and drilldown filters', () => {
      renderWithRouter(<NationalDashboardPage />);
      expect(screen.getByText(/National Health Resource Command/i)).toBeInTheDocument();
      expect(screen.getByText(/National Bed Occupancy/i)).toBeInTheDocument();
      expect(screen.getByText(/National Medicine Runway/i)).toBeInTheDocument();
      expect(screen.getByText(/State Resilience & Resource Benchmarks/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Export PDF Bulletin/i })).toBeInTheDocument();
    });
  });

  describe('Phase 4 — Geospatial Map & Heatmaps', () => {
    it('renders resource map with district filter, warehouse markers, and heatmap layer toggles', () => {
      renderWithRouter(<InteractiveResourceMap />);
      expect(screen.getByText(/Geospatial Healthcare Network Telemetry/i)).toBeInTheDocument();

      // Check Heatmap layer buttons
      expect(screen.getByRole('button', { name: /Disease Heatmap/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Emergency Heatmap/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Warehouses & MSDs/i })).toBeInTheDocument();

      // Toggle Disease Heatmap
      const diseaseBtn = screen.getByRole('button', { name: /Disease Heatmap/i });
      fireEvent.click(diseaseBtn);
      expect(screen.getByText(/Disease Surveillance Zone/i)).toBeInTheDocument();
    });
  });

  describe('Feature 23 — Warehouse Dashboard UI', () => {
    it('renders warehouse network, cold-chain capacity and live dispatch queue', () => {
      renderWithRouter(<WarehouseDashboardPage />);
      expect(screen.getByText(/Warehouse Network & Cold-Chain Capacity Dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/Total Pallet Capacity/i)).toBeInTheDocument();
      expect(screen.getByText(/Cold-Chain Volume/i)).toBeInTheDocument();
      expect(screen.getByText(/Live Logistics & Redistribution Dispatch Queue/i)).toBeInTheDocument();
    });
  });

  describe('Phase 5 — Granular Batches, Expiry Tracker & Barcode Scanner', () => {
    it('switches to Batch Directory tab and displays batch table', () => {
      renderWithRouter(<InventoryPage />);
      const batchTab = screen.getByRole('button', { name: /Batch Directory/i });
      fireEvent.click(batchTab);

      expect(screen.getByText(/Granular Batch Registry & Cold-Chain Vault/i)).toBeInTheDocument();
      expect(screen.getByText(/IN-2026-X88/i)).toBeInTheDocument();
    });

    it('switches to Expiry Tracker tab and displays FEFO protocol table', () => {
      renderWithRouter(<InventoryPage />);
      const expiryTab = screen.getByRole('button', { name: /Expiry Tracker/i });
      fireEvent.click(expiryTab);

      expect(screen.getByText(/Near-Expiry Medicine Ledger \(FEFO Protocol\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Monetary Wastage Risk Value/i)).toBeInTheDocument();
    });

    it('switches to Optical Scanner tab and handles barcode scan recognition', () => {
      renderWithRouter(<InventoryPage />);
      const scanTab = screen.getByRole('button', { name: /Optical Scanner/i });
      fireEvent.click(scanTab);

      expect(screen.getByText(/Optical Camera & Barcode Reader/i)).toBeInTheDocument();
      const sampleScanBtn = screen.getAllByRole('button', { name: /Scan:/i })[0];
      fireEvent.click(sampleScanBtn);

      expect(screen.getByText(/Identified Pharmaceutical Lot/i)).toBeInTheDocument();
    });
  });

  describe('Phase 6 — Personnel Directory & Biometric Attendance', () => {
    it('switches between Doctor-to-Patient Ratios, Personnel, and Attendance tabs', () => {
      renderWithRouter(<WorkforcePage />);
      expect(screen.getByText(/WHO Guideline Benchmark: 1 Doctor per 1,000 Population/i)).toBeInTheDocument();

      // Personnel Directory tab
      const personnelTab = screen.getByRole('button', { name: /Personnel Directory/i });
      fireEvent.click(personnelTab);
      expect(screen.getByText(/Dr\. Vikramaditya Sen/i)).toBeInTheDocument();

      // Attendance tab
      const attendanceTab = screen.getByRole('button', { name: /Biometric Attendance/i });
      fireEvent.click(attendanceTab);
      expect(screen.getByText(/Live Biometric Attendance Stream/i)).toBeInTheDocument();
      expect(screen.getAllByText(/RFID \+ Iris Verified/i).length).toBeGreaterThan(0);
    });
  });

  describe('Phase 9 — Federated AI Local Model Accuracy', () => {
    it('displays active & offline nodes and local vs global model accuracy table', () => {
      renderWithRouter(<FederatedAIPage />);
      expect(screen.getByText(/Federated AI Collaborative Learning Network/i)).toBeInTheDocument();
      expect(screen.getByText(/Current Training Round/i)).toBeInTheDocument();
      expect(screen.getByText(/Local Model Accuracy vs Global Model/i)).toBeInTheDocument();
      expect(screen.getByText(/AIIMS New Delhi Trauma Edge Node/i)).toBeInTheDocument();
      expect(screen.getByText(/Zero Clinical EHR Data Egress Architecture/i)).toBeInTheDocument();
    });
  });

  describe('Analytics & Optimization (Features 62-70)', () => {
    it('renders Historical Trends, Wastage Reduction, Resilience, and District Comparison', () => {
      renderWithRouter(<AIDashboard />);
      expect(screen.getByText(/Analytics, Predictive AI & Supply Chain Resilience/i)).toBeInTheDocument();
      expect(screen.getByText(/SHAP AI Feature Attribution & Explainability Panel/i)).toBeInTheDocument();

      // Historical Trends
      const trendsTab = screen.getByRole('button', { name: /Historical Trend & Utilization/i });
      fireEvent.click(trendsTab);
      expect(screen.getByText(/9-Month Healthcare Resource Consumption & Bed Utilization/i)).toBeInTheDocument();

      // Cost & Wastage
      const costTab = screen.getByRole('button', { name: /Cost & Wastage Reduction/i });
      fireEvent.click(costTab);
      expect(screen.getByText(/Total Wastage Prevented \(YTD\)/i)).toBeInTheDocument();
      expect(screen.getByText(/₹42.8 Lakhs/i)).toBeInTheDocument();

      // Resilience & Risk
      const resilienceTab = screen.getByRole('button', { name: /Resilience & Risk Scores/i });
      fireEvent.click(resilienceTab);
      expect(screen.getByText(/Supply Chain Resilience Score Breakdown/i)).toBeInTheDocument();

      // District Comparison
      const compTab = screen.getByRole('button', { name: /District Comparison & Benchmarking/i });
      fireEvent.click(compTab);
      expect(screen.getByText(/Inter-District Health Grid Performance Scorecard/i)).toBeInTheDocument();
    });
  });
});
