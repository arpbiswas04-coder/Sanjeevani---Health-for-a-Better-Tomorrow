// LEGACY DEMONSTRATION ONLY: not mounted by the current application router.
import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useHealth } from '@/hooks/useHealth';
import { useToast } from '@/hooks/useToast';
import { useUIStore } from '@/store/uiStore';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  Server,
  Building2,
  Package,
  Bed,
  Cpu,
  CheckCircle2,
  Sparkles,
  Command,
  BellRing,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { data: health, isLoading, isError } = useHealth();
  const toast = useToast();
  const { setCommandPaletteOpen, activeRole, theme } = useUIStore();
  const { t } = useTranslation();

  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  const kpis = [
    {
      title: 'Connected Health Facilities',
      value: '1,428',
      change: '+12 this week',
      icon: <Building2 className="w-5 h-5 text-emerald-400" />,
      badge: '99.8% Online',
    },
    {
      title: 'Monitored Critical Stock',
      value: '2.84M units',
      change: '14 low stock alerts',
      icon: <Package className="w-5 h-5 text-amber-400" />,
      badge: 'Live RFID/QR',
    },
    {
      title: 'ICU & Ventilator Capacity',
      value: '82.4%',
      change: '1,120 beds vacant',
      icon: <Bed className="w-5 h-5 text-purple-400" />,
      badge: 'Normal Range',
    },
    {
      title: 'Federated Model Accuracy',
      value: '96.2%',
      change: 'Round #42 Completed',
      icon: <Cpu className="w-5 h-5 text-cyan-400" />,
      badge: 'Privacy Safe',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl p-8 sm:p-10 border border-emerald-500/20 bg-gradient-to-br from-slate-900 via-slate-900/90 to-emerald-950/30 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Member 1 Phase 1 — Foundation Completed</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight bg-gradient-to-r from-emerald-400 via-teal-200 to-cyan-400 bg-clip-text text-transparent">
            {t('app.name')}
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed font-normal">
            {t('app.subtitle')} — Decentralized command mesh connecting primary health centers,
            district hospitals, and state medical store depots with AI-driven inventory resilience.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all hover:scale-105 active:scale-95"
            >
              <Command className="w-4 h-4" />
              <span>Launch Command Palette (Ctrl+K)</span>
            </button>

            <button
              onClick={() => setIsDemoModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 hover:border-slate-600 transition-all"
            >
              <span>Test Modal Dialog</span>
            </button>

            <button
              onClick={() => {
                toast.success(
                  'Supply Alert Resolved',
                  'Oxygen cylinder replenishment dispatched to District Hospital Kanpur.',
                  4000
                );
              }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 hover:border-slate-600 transition-all"
            >
              <BellRing className="w-3.5 h-3.5 text-emerald-400" />
              <span>Test Toast Notification</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi) => (
          <Card
            key={kpi.title}
            className="flex flex-col justify-between hover:border-slate-600/80 transition-all duration-200 group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 rounded-xl bg-slate-900 border border-slate-700/60 group-hover:scale-110 transition-transform">
                  {kpi.icon}
                </div>
                <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-slate-900 text-slate-400 border border-slate-800">
                  {kpi.badge}
                </span>
              </div>
              <h3 className="text-xs font-medium text-slate-400">{kpi.title}</h3>
              <div className="text-2xl font-bold text-slate-100 mt-1 font-mono tracking-tight">
                {kpi.value}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] text-emerald-400 flex items-center justify-between">
              <span>{kpi.change}</span>
              <Activity className="w-3.5 h-3.5 opacity-60" />
            </div>
          </Card>
        ))}
      </div>

      {/* System Status and Architecture Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Backend API Health Status */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Server className="w-4 h-4 text-emerald-400" />
                Backend Telemetry API
              </span>
              {isLoading && <Badge level="info">Checking...</Badge>}
              {isError && <Badge level="critical">Offline / Unreachable</Badge>}
              {health && <Badge level="success">Operational</Badge>}
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              FastAPI backend running on port 8000 with PostgreSQL 16 connection pooling and Redis 7 cache.
            </p>
          </div>

          <div className="mt-4 p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-xs font-mono text-slate-300">
            {health ? (
              <pre className="text-[11px] text-emerald-300">{JSON.stringify(health, null, 2)}</pre>
            ) : (
              <span className="text-slate-500">Awaiting response from /api/v1/health...</span>
            )}
          </div>
        </Card>

        {/* Phase 1 Verification Checklist */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Phase 1 — Foundation Checklist Verification
            </h3>
            <span className="text-xs text-slate-400 font-mono">Role: {activeRole}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">App Shell & Responsive Layout</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Fluid responsive layout with collapsible sidebar and mobile bottom navbar.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Toast & Modal Systems</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Zustand-powered reactive toast queue and accessible modal dialogs.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Multilingual (i18next)</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  English (en), Hindi (hi), and Bengali (bn) locale bundles integrated.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-200">Quick Command Palette</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Global search and command palette bound to <kbd className="font-mono">Ctrl+K</kbd>.
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Demo Modal Dialog */}
      <Modal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        title="Sanjeevani Grid — System Modal System"
      >
        <div className="space-y-4 text-slate-300 text-xs leading-relaxed">
          <p>
            This modal demonstrates the accessible, backdrop-blurred dialog system created for
            Phase 1 Foundation. It supports keyboard accessibility (<kbd className="font-mono">ESC</kbd> to dismiss), click-outside dismissal, and responsive max-width sizing.
          </p>

          <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1.5 font-mono text-[11px]">
            <div className="text-emerald-400">Current Theme: {theme}</div>
            <div className="text-teal-400">Current Simulated Role: {activeRole}</div>
            <div className="text-slate-400">Framework: React 18 + Vite + Tailwind CSS</div>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              onClick={() => setIsDemoModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-semibold transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => {
                setIsDemoModalOpen(false);
                toast.info('Acknowledged', 'Modal action confirmed successfully.');
              }}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-md shadow-emerald-500/20 transition-colors"
            >
              Confirm Action
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
