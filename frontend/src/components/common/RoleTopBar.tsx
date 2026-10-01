import React, { useState } from 'react';
import { useUIStore } from '@/store/uiStore';
import { useAuthStore } from '@/store/authStore';
import { ROLE_LABELS } from '@/types/auth';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import {
  Menu,
  Bell,
  Sun,
  Moon,
  Command,
  Globe,
  LogOut,
  User as UserIcon,
  Settings,
  MapPin,
  ChevronDown,
  ShieldCheck,
} from 'lucide-react';

export const RoleTopBar: React.FC = () => {
  const { theme, toggleTheme, setCommandPaletteOpen, setMobileSidebarOpen } = useUIStore();
  const { user, role, logout } = useAuthStore();
  const { i18n, t } = useTranslation();
  const navigate = useNavigate();

  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    setIsLangMenuOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Determine current scope based on role and user assignment
  const getScopeLabel = (): { title: string; subtitle: string } => {
    switch (role) {
      case 'SUPER_ADMIN':
        return {
          title: 'System Infrastructure',
          subtitle: 'Zero-Trust Central Mesh',
        };
      case 'NATIONAL_ADMIN':
        return {
          title: 'National Command',
          subtitle: 'Republic of India (All States & UTs)',
        };
      case 'STATE_ADMIN':
        return {
          title: user?.state || 'State Jurisdiction',
          subtitle: 'State Health Authority',
        };
      case 'DISTRICT_ADMIN':
        return {
          title: `${user?.district || 'District'} District`,
          subtitle: user?.state || 'State Health Sub-Division',
        };
      case 'FACILITY_ADMIN':
        return {
          title: user?.facilityName || 'Primary Health Center',
          subtitle: `${user?.district || 'District'}, ${user?.state || 'State'}`,
        };
      default:
        return {
          title: 'Sanjeevani Grid',
          subtitle: 'Health Resource Network',
        };
    }
  };

  const scope = getScopeLabel();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Left: Mobile hamburger & Scope Indicator */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800 lg:hidden"
          aria-label="Open navigation drawer"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Current Scope Banner */}
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hidden sm:flex">
            <MapPin className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-xs sm:text-sm font-bold text-slate-100 leading-tight">
                {scope.title}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-teal-300 border border-slate-700 hidden md:inline-block">
                {role ? ROLE_LABELS[role] : 'Command'}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 hidden sm:inline-block">
              {scope.subtitle}
            </span>
          </div>
        </div>
      </div>

      {/* Right Actions: Command Palette, Language, Theme, Notifications, User Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Quick Command Palette Button */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 text-xs transition-colors"
          title="Command Palette"
        >
          <Command className="w-3.5 h-3.5" />
          <span>Quick Jump</span>
          <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 border border-slate-700 rounded text-slate-400">
            Ctrl+K
          </kbd>
        </button>

        {/* Language Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
            className="flex items-center gap-1.5 p-2 sm:px-2.5 sm:py-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 text-xs border border-transparent hover:border-slate-700 transition-colors"
            title="Switch Language"
          >
            <Globe className="w-4 h-4" />
            <span className="hidden sm:inline uppercase text-xs font-mono font-bold">
              {i18n.language.slice(0, 2)}
            </span>
          </button>

          {isLangMenuOpen && (
            <div className="absolute right-0 mt-2 w-32 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-1 z-50 animate-in fade-in zoom-in-95">
              <button
                onClick={() => handleLanguageChange('en')}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-800 flex items-center justify-between ${
                  i18n.language.startsWith('en') ? 'text-emerald-400 font-bold' : 'text-slate-300'
                }`}
              >
                <span>English</span>
                <span className="text-[10px] font-mono text-slate-500">EN</span>
              </button>
              <button
                onClick={() => handleLanguageChange('hi')}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-800 flex items-center justify-between ${
                  i18n.language.startsWith('hi') ? 'text-emerald-400 font-bold' : 'text-slate-300'
                }`}
              >
                <span>हिन्दी</span>
                <span className="text-[10px] font-mono text-slate-500">HI</span>
              </button>
              <button
                onClick={() => handleLanguageChange('bn')}
                className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-800 flex items-center justify-between ${
                  i18n.language.startsWith('bn') ? 'text-emerald-400 font-bold' : 'text-slate-300'
                }`}
              >
                <span>বাংলা</span>
                <span className="text-[10px] font-mono text-slate-500">BN</span>
              </button>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          aria-label="Toggle visual theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Alerts / Notifications */}
        <Link
          to={role === 'SUPER_ADMIN' ? '/admin/audit-logs' : `/${role?.split('_')[0].toLowerCase()}/alerts`}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 relative transition-colors"
          title="Notifications & Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-slate-900" />
        </Link>

        {/* User Identity Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
            className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl hover:bg-slate-800 text-slate-200 text-xs transition-colors border border-transparent hover:border-slate-700"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center font-bold text-slate-950 text-xs shadow-sm">
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="font-bold text-slate-200 truncate max-w-[120px]">
                {user?.name || 'Officer'}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {role ? ROLE_LABELS[role] : 'User'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:inline" />
          </button>

          {isProfileMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 space-y-1">
              <div className="px-4 py-2 border-b border-slate-800">
                <div className="font-bold text-slate-100 text-xs">{user?.name}</div>
                <div className="text-[11px] text-slate-400 truncate">{user?.email}</div>
                <div className="mt-1 text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  {role ? ROLE_LABELS[role] : ''}
                </div>
              </div>

              <Link
                to="/profile"
                onClick={() => setIsProfileMenuOpen(false)}
                className="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-colors"
              >
                <UserIcon className="w-4 h-4 text-slate-400" />
                <span>Officer Profile</span>
              </Link>

              <Link
                to="/settings"
                onClick={() => setIsProfileMenuOpen(false)}
                className="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-colors"
              >
                <Settings className="w-4 h-4 text-slate-400" />
                <span>Security Settings</span>
              </Link>

              <div className="border-t border-slate-800 pt-1">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default RoleTopBar;
