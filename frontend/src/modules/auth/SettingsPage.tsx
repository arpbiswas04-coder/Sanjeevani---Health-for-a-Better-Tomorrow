import React, { useState } from 'react';
import { DetailPanel } from '@/components/common/BackendData';
import { Card } from '@/components/ui/Card';
import { useUIStore } from '@/store/uiStore';
import { useToast } from '@/hooks/useToast';
import { Settings, Moon, Sun, Bell, Volume2, Wifi, Shield, Eye, Save } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, toggleTheme } = useUIStore();
  const [highContrast, setHighContrast] = useState(false);
  const [soundAlerts, setSoundAlerts] = useState(true);
  const [offlineSyncInterval, setOfflineSyncInterval] = useState('30s');
  const toast = useToast();

  const handleSave = () => {
    toast.info('Not connected', 'Only the browser theme is currently applied. Alert audio, enhanced contrast and offline synchronization settings are not implemented.');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100">Platform Settings & Accessibility</h2>
        <p className="text-xs text-slate-400">Browser-local theme preferences. Disabled settings below are not connected to the backend.</p>
      </div>

      <div className="space-y-4">
        <DetailPanel title="Public backend configuration" path="/admin/config" permission="admin.config" />
        {/* Appearance & Accessibility */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-2">
            <Eye className="w-4 h-4 text-emerald-400" />
            <span>Display & Accessibility (WCAG 2.1 AA)</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">Color Theme</span>
                <p className="text-slate-400 text-[11px]">Toggle between High-Contrast Dark Mode and Clean Light Mode</p>
              </div>
              <button
                onClick={toggleTheme}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 flex items-center gap-2"
              >
                {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
                <span className="capitalize">{theme} Theme</span>
              </button>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
              <div>
                <span className="font-semibold text-slate-200">Enhanced High-Contrast Borders</span>
                <p className="text-slate-400 text-[11px]">Increases component border opacity for enhanced optical visibility</p>
              </div>
              <input
                type="checkbox"
                disabled
                checked={highContrast}
                onChange={(e) => setHighContrast(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
              />
            </div>
          </div>
        </Card>

        {/* Telemetry & Audio */}
        <Card className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 border-b border-slate-800 pb-2">
            <Volume2 className="w-4 h-4 text-cyan-400" />
            <span>Audio & Critical Alerts</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">Audible Alarm on DEFCON-1 Emergency</span>
                <p className="text-slate-400 text-[11px]">Play audio ping when ICU beds reach critical saturation threshold (&gt;95%)</p>
              </div>
              <input
                type="checkbox"
                disabled
                checked={soundAlerts}
                onChange={(e) => setSoundAlerts(e.target.checked)}
                className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
              <div>
                <span className="font-semibold text-slate-200">Offline Sync Frequency</span>
                <p className="text-slate-400 text-[11px]">Heartbeat interval for flushing IndexedDB action queue to backend</p>
              </div>
              <select
                disabled
                value={offlineSyncInterval}
                onChange={(e) => setOfflineSyncInterval(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none font-mono"
              >
                <option value="10s">10 seconds (High Precision)</option>
                <option value="30s">30 seconds (Balanced)</option>
                <option value="60s">60 seconds (Low Bandwidth)</option>
              </select>
            </div>
          </div>
        </Card>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleSave}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:scale-105"
          >
            <Save className="w-4 h-4" />
            <span>Settings Availability</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
