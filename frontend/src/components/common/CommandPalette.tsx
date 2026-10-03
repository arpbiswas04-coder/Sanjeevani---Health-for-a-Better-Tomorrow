import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { canAccessPath } from '@/app/authorization';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import { useTranslation } from 'react-i18next';
import {
  Search,
  LayoutDashboard,
  Map,
  Building2,
  Package,
  Bed,
  Users,
  AlertTriangle,
  Cpu,
  BarChart3,
  Moon,
  Sun,
  Shield,
  X,
} from 'lucide-react';

export const CommandPalette: React.FC = () => {
  const { isCommandPaletteOpen, setCommandPaletteOpen, toggleTheme, theme, setActiveRole, activeRole } =
    useUIStore();
  const user = useAuthStore(state => state.user);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!isCommandPaletteOpen);
      }
      if (e.key === 'Escape' && isCommandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, setCommandPaletteOpen]);

  if (!isCommandPaletteOpen) return null;

  const navigationItems = [
    { label: t('nav.nationalDashboard'), path: '/', icon: <LayoutDashboard className="w-4 h-4 text-emerald-400" />, category: 'Navigation' },
    { label: t('nav.resourceMap'), path: '/map', icon: <Map className="w-4 h-4 text-cyan-400" />, category: 'Navigation' },
    { label: t('nav.facilities'), path: '/facilities', icon: <Building2 className="w-4 h-4 text-blue-400" />, category: 'Navigation' },
    { label: t('nav.inventory'), path: '/inventory', icon: <Package className="w-4 h-4 text-amber-400" />, category: 'Navigation' },
    { label: t('nav.bedAvailability'), path: '/beds', icon: <Bed className="w-4 h-4 text-purple-400" />, category: 'Navigation' },
    { label: t('nav.workforce'), path: '/workforce', icon: <Users className="w-4 h-4 text-pink-400" />, category: 'Navigation' },
    { label: t('nav.emergencyCommand'), path: '/emergency', icon: <AlertTriangle className="w-4 h-4 text-rose-400" />, category: 'Crisis' },
    { label: t('nav.federatedAI'), path: '/federated-ai', icon: <Cpu className="w-4 h-4 text-teal-400" />, category: 'Intelligence' },
    { label: t('nav.analytics'), path: '/analytics', icon: <BarChart3 className="w-4 h-4 text-indigo-400" />, category: 'Intelligence' },
  ];

  const filteredItems = navigationItems.filter((item) =>
    (item.path === '/' || canAccessPath(item.path, user)) && item.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (path: string) => {
    navigate(path);
    setCommandPaletteOpen(false);
    setQuery('');
  };

  return (
    <div className="fixed inset-0 z-[1000] flex items-start justify-center pt-20 px-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={() => setCommandPaletteOpen(false)}
      />

      {/* Palette Container */}
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden z-10 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center px-4 py-3.5 border-b border-slate-800 gap-3">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder={t('actions.searchPlaceholder')}
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <button
            onClick={() => setCommandPaletteOpen(false)}
            className="text-slate-500 hover:text-slate-300 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          <div className="px-3 py-1.5 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Quick Navigation
          </div>
          {filteredItems.map((item) => (
            <button
              key={item.label}
              onClick={() => handleSelect(item.path)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/80 hover:text-white transition-colors group text-left"
            >
              <div className="flex items-center gap-3">
                {item.icon}
                <span>{item.label}</span>
              </div>
              <span className="text-xs text-slate-500 group-hover:text-slate-400 font-mono">Jump &rarr;</span>
            </button>
          ))}

          {filteredItems.length === 0 && (
            <div className="text-center py-8 text-sm text-slate-500">
              No matching commands found for "{query}"
            </div>
          )}

          <div className="pt-2 border-t border-slate-800 mt-2">
            <div className="px-3 py-1.5 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
              Quick Actions
            </div>
            <button
              onClick={() => {
                toggleTheme();
                setCommandPaletteOpen(false);
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800 transition-colors"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-4 h-4 text-amber-400" />
                  <span>Switch to Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4 text-indigo-400" />
                  <span>Switch to Dark Mode</span>
                </>
              )}
            </button>

          </div>
        </div>

        <div className="px-4 py-2 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
          <span>Navigate with <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">↑</kbd> <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">↓</kbd></span>
          <span>Close with <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">ESC</kbd></span>
        </div>
      </div>
    </div>
  );
};
