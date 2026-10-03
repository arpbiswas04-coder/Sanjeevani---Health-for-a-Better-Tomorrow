// LEGACY DEMONSTRATION ONLY: not mounted by the current application router.
import React, { useState } from 'react';
import { useUIStore, UserRole } from '@/store/uiStore';
import { useTranslation } from 'react-i18next';
import {
  Menu,
  Search,
  Moon,
  Sun,
  Bell,
  Globe,
  Shield,
  Radio,
  ChevronDown,
} from 'lucide-react';

export const TopBar: React.FC = () => {
  const {
    toggleSidebar,
    setMobileSidebarOpen,
    isMobileSidebarOpen,
    theme,
    toggleTheme,
    setCommandPaletteOpen,
    activeRole,
    setActiveRole,
  } = useUIStore();
  const { t, i18n } = useTranslation();
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false);
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);

  const roles: { id: UserRole; label: string }[] = [
    { id: 'national_officer', label: t('roles.national_officer') },
    { id: 'state_officer', label: t('roles.state_officer') },
    { id: 'district_officer', label: t('roles.district_officer') },
    { id: 'facility_admin', label: t('roles.facility_admin') },
    { id: 'logistics_coordinator', label: t('roles.logistics_coordinator') },
    { id: 'doctor', label: t('roles.doctor') },
  ];

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'हिन्दी' },
    { code: 'bn', label: 'বাংলা' },
  ];

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
    setIsLangDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 h-16 w-full border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
      {/* Left section: toggles and search */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => {
            if (window.innerWidth < 1024) {
              setMobileSidebarOpen(!isMobileSidebarOpen);
            } else {
              toggleSidebar();
            }
          }}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
          aria-label="Toggle Navigation Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search Bar */}
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 text-xs text-slate-400 hover:text-slate-200 transition-all w-60 md:w-80 group text-left"
        >
          <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200 transition-colors" />
          <span className="flex-1 truncate">{t('actions.searchPlaceholder')}</span>
          <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-slate-900/80 text-slate-400 rounded border border-slate-700/80">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right section: System telemetry, language, theme, role, notifications */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Status indicator */}
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <Radio className="w-3.5 h-3.5 animate-pulse" />
          <span>{t('app.onlineStatus')}</span>
        </div>

        {/* Role Selector dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-xs font-medium text-slate-200 transition-colors"
            title="Switch Simulated Role"
          >
            <Shield className="w-3.5 h-3.5 text-teal-400" />
            <span className="hidden md:inline max-w-[120px] truncate">
              {roles.find((r) => r.id === activeRole)?.label || activeRole}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {isRoleDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-3 py-1.5 text-[10px] uppercase font-semibold text-slate-500 tracking-wider">
                Simulated User Role
              </div>
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    setActiveRole(r.id);
                    setIsRoleDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800 transition-colors ${
                    activeRole === r.id ? 'text-emerald-400 font-semibold bg-emerald-500/10' : 'text-slate-300'
                  }`}
                >
                  <span>{r.label}</span>
                  {activeRole === r.id && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Language selector */}
        <div className="relative">
          <button
            onClick={() => setIsLangDropdownOpen(!isLangDropdownOpen)}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors flex items-center gap-1"
            aria-label="Change Language"
          >
            <Globe className="w-4 h-4" />
            <span className="text-xs uppercase font-mono">{i18n.language.substring(0, 2)}</span>
          </button>

          {isLangDropdownOpen && (
            <div className="absolute right-0 mt-2 w-32 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1 z-50 animate-in fade-in zoom-in-95 duration-150">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => handleLanguageChange(l.code)}
                  className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-800 transition-colors ${
                    i18n.language.startsWith(l.code)
                      ? 'text-emerald-400 font-semibold bg-emerald-500/10'
                      : 'text-slate-300'
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-400" />
          )}
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors relative"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-slate-900" />
          </button>
        </div>

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-xs font-bold text-slate-950 shadow-md shadow-emerald-500/20">
            SG
          </div>
        </div>
      </div>
    </header>
  );
};
