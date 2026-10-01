import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Map, Package, AlertTriangle, Menu } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';

export const Navbar: React.FC = () => {
  const { setMobileSidebarOpen, isMobileSidebarOpen } = useUIStore();

  const mobileNav = [
    { name: 'Command', path: '/', icon: LayoutDashboard },
    { name: 'Live Map', path: '/map', icon: Map },
    { name: 'Stock', path: '/inventory', icon: Package },
    { name: 'Crisis', path: '/emergency', icon: AlertTriangle, alert: true },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/90 backdrop-blur-md border-t border-slate-800 px-4 py-2 flex items-center justify-around">
      {mobileNav.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 py-1 px-2 rounded-lg text-[10px] font-medium transition-colors ${
                isActive
                  ? 'text-emerald-400 font-semibold'
                  : item.alert
                  ? 'text-rose-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            <span>{item.name}</span>
          </NavLink>
        );
      })}
      <button
        onClick={() => setMobileSidebarOpen(!isMobileSidebarOpen)}
        className="flex flex-col items-center gap-1 py-1 px-2 rounded-lg text-[10px] font-medium text-slate-400 hover:text-slate-200"
      >
        <Menu className="w-4 h-4" />
        <span>Menu</span>
      </button>
    </nav>
  );
};
