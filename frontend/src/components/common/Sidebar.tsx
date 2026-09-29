import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import { useTranslation } from 'react-i18next';
import {
  Activity,
  LayoutDashboard,
  Map,
  Building2,
  Package,
  Clock,
  Bed,
  Users,
  UserCheck,
  TrendingUp,
  AlertTriangle,
  Cpu,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
  Layers,
  Wrench,
  Bell,
  User,
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  alert?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC = () => {
  const { isSidebarCollapsed, toggleSidebar, isMobileSidebarOpen, setMobileSidebarOpen } =
    useUIStore();
  const location = useLocation();
  const { t } = useTranslation();

  const navSections: NavSection[] = [
    {
      title: 'Command',
      items: [
        { name: t('nav.nationalDashboard'), path: '/', icon: LayoutDashboard },
        { name: 'Regional Command', path: '/dashboard/regional', icon: Layers, badge: 'States' },
        { name: t('nav.resourceMap'), path: '/map', icon: Map, badge: 'Live GPS' },
      ],
    },
    {
      title: 'Operations',
      items: [
        { name: t('nav.facilities'), path: '/facilities', icon: Building2 },
        { name: t('nav.inventory'), path: '/inventory', icon: Package },
        { name: t('nav.expiryTracking'), path: '/expiry', icon: Clock },
        { name: t('nav.bedAvailability'), path: '/beds', icon: Bed },
        { name: t('nav.workforce'), path: '/workforce', icon: Users },
        { name: 'Biomed Equipment', path: '/equipment', icon: Wrench },
      ],
    },
    {
      title: 'Clinical & Surge',
      items: [
        { name: t('nav.patients'), path: '/patients', icon: UserCheck },
        { name: t('nav.diseaseTrends'), path: '/disease', icon: TrendingUp },
        {
          name: t('nav.emergencyCommand'),
          path: '/emergency',
          icon: AlertTriangle,
          alert: true,
        },
        {
          name: 'Alert Management',
          path: '/alerts',
          icon: Bell,
          badge: 'Push',
        },
      ],
    },
    {
      title: 'Intelligence',
      items: [
        { name: t('nav.federatedAI'), path: '/federated-ai', icon: Cpu, badge: 'FedML' },
        { name: t('nav.analytics'), path: '/analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'System',
      items: [
        { name: 'Admin & RBAC', path: '/admin', icon: ShieldCheck, badge: 'F-104' },
        { name: 'User Profile', path: '/profile', icon: User },
        { name: t('nav.settings'), path: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col bg-slate-900 border-r border-slate-800 transition-all duration-300 ease-in-out ${
          isSidebarCollapsed ? 'w-20' : 'w-64'
        } ${
          isMobileSidebarOpen
            ? 'translate-x-0'
            : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo and Brand */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
          <NavLink
            to="/"
            onClick={() => setMobileSidebarOpen(false)}
            className="flex items-center gap-3 overflow-hidden"
          >
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shrink-0">
              <Activity className="w-5 h-5" />
            </div>
            {!isSidebarCollapsed && (
              <div className="flex flex-col truncate">
                <span className="font-extrabold text-sm tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent truncate">
                  Sanjeevani Grid
                </span>
                <span className="text-[10px] text-slate-400 truncate">
                  Health Resilience OS
                </span>
              </div>
            )}
          </NavLink>

          {/* Mobile close button */}
          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items List */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
          {navSections.map((section) => (
            <div key={section.title} className="space-y-1">
              {!isSidebarCollapsed && (
                <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  {section.title}
                </div>
              )}
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileSidebarOpen(false)}
                    title={isSidebarCollapsed ? item.name : undefined}
                    className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all group relative ${
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/10 font-semibold'
                        : item.alert
                        ? 'text-rose-400 hover:bg-rose-500/10 hover:text-rose-300'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${
                        isActive
                          ? 'text-emerald-400'
                          : item.alert
                          ? 'text-rose-400'
                          : 'text-slate-400 group-hover:text-slate-200'
                      }`}
                    />

                    {!isSidebarCollapsed && (
                      <span className="truncate flex-1">{item.name}</span>
                    )}

                    {!isSidebarCollapsed && item.badge && (
                      <span className="px-1.5 py-0.5 text-[9px] font-mono rounded bg-slate-800 text-teal-300 border border-slate-700">
                        {item.badge}
                      </span>
                    )}

                    {!isSidebarCollapsed && item.alert && (
                      <span className="flex h-2 w-2 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                      </span>
                    )}

                    {/* Active Route Left Pill */}
                    {isActive && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-emerald-400" />
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer: Grid Resilience Metric & Collapse Toggle */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
          {!isSidebarCollapsed ? (
            <div className="p-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <div className="flex flex-col">
                  <span className="text-[10px] text-slate-400">{t('status.resilienceScore')}</span>
                  <span className="text-xs font-bold text-slate-100 font-mono">94.2% (Resilient)</span>
                </div>
              </div>
              <button
                onClick={toggleSidebar}
                className="hidden lg:flex p-1 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-slate-200"
                aria-label="Collapse Sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <button
                onClick={toggleSidebar}
                className="hidden lg:flex p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200"
                aria-label="Expand Sidebar"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
