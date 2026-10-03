import React from 'react';
import { Role } from '@/types/auth';
import {
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
  ShieldCheck,
  Server,
  Layers,
  FileText,
  Truck,
  Wrench,
  User as UserIcon,
} from 'lucide-react';

export interface NavItemConfig {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  alert?: boolean;
}

export interface NavSectionConfig {
  title: string;
  items: NavItemConfig[];
}

export const NAVIGATION_BY_ROLE: Record<Role, NavSectionConfig[]> = {
  SUPER_ADMIN: [
    {
      title: 'Operational Data',
      items: [
        { name: 'Resource Map', path: '/map', icon: Map },
        { name: 'Inventory', path: '/inventory', icon: Package },
        { name: 'Supply Chain', path: '/warehouses', icon: Truck },
        { name: 'Workforce', path: '/workforce', icon: Users },
        { name: 'Operational Alerts', path: '/alerts', icon: AlertTriangle },
        { name: 'Reports & Analytics', path: '/analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'System Management',
      items: [
        { name: 'Admin Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
        { name: 'Users & Personnel', path: '/admin/users', icon: Users },
        { name: 'Roles & Permissions', path: '/admin/roles', icon: ShieldCheck, badge: 'RBAC' },
        { name: 'System Configuration', path: '/admin/config', icon: Settings },
      ],
    },
    {
      title: 'Jurisdictions',
      items: [
        { name: 'National Command', path: '/national/dashboard', icon: Layers },
        { name: 'Facility Directory', path: '/admin/facilities', icon: Building2 },
      ],
    },
    {
      title: 'Infrastructure',
      items: [
        { name: 'System Monitoring', path: '/admin/monitoring', icon: Server, badge: 'Live' },
        { name: 'Audit Logs', path: '/admin/audit-logs', icon: FileText },
        { name: 'Platform Settings', path: '/admin/settings', icon: Settings },
      ],
    },
  ],

  NATIONAL_ADMIN: [
    {
      title: 'National Command',
      items: [
        { name: 'National Command', path: '/national/dashboard', icon: LayoutDashboard },
        { name: 'National Resource Map', path: '/national/map', icon: Map, badge: 'GPS' },
        { name: 'State Telemetry', path: '/national/states', icon: Layers },
        { name: 'District Comparison', path: '/national/district-comparison', icon: BarChart3 },
      ],
    },
    {
      title: 'National Logistics',
      items: [
        { name: 'Facilities Directory', path: '/national/facilities', icon: Building2 },
        { name: 'Stock Inventory', path: '/national/inventory', icon: Package },
        { name: 'Regional Depots', path: '/national/warehouses', icon: Building2 },
        { name: 'Bed Availability', path: '/national/beds', icon: Bed },
        { name: 'Workforce Roster', path: '/national/workforce', icon: Users },
      ],
    },
    {
      title: 'Clinical & Surge',
      items: [
        { name: 'Patient Footfall', path: '/national/patients', icon: UserCheck },
        { name: 'Disease Outbreaks', path: '/national/disease', icon: TrendingUp },
        { name: 'Emergency Command', path: '/national/emergency', icon: AlertTriangle, alert: true },
        { name: 'Push Alerts', path: '/national/alerts', icon: AlertTriangle },
      ],
    },
    {
      title: 'AI & Intelligence',
      items: [
        { name: 'AI Demand Forecast', path: '/national/forecasting', icon: TrendingUp },
        { name: 'Federated AI Mesh', path: '/national/federated-ai', icon: Cpu, badge: 'FedML' },
        { name: 'Analytics Hub', path: '/national/analytics', icon: BarChart3 },
      ],
    },
  ],

  STATE_ADMIN: [
    {
      title: 'State Health Command',
      items: [
        { name: 'State Command', path: '/state/dashboard', icon: LayoutDashboard },
        { name: 'State Resource Map', path: '/state/map', icon: Map, badge: 'State GPS' },
        { name: 'Districts Directory', path: '/state/districts', icon: Layers },
        { name: 'State Facilities', path: '/state/facilities', icon: Building2 },
      ],
    },
    {
      title: 'State Operations',
      items: [
        { name: 'State Inventory', path: '/state/inventory', icon: Package },
        { name: 'Bed Surges', path: '/state/beds', icon: Bed },
        { name: 'State Workforce', path: '/state/workforce', icon: Users },
      ],
    },
    {
      title: 'Surveillance & Crisis',
      items: [
        { name: 'Patient Influx', path: '/state/patients', icon: UserCheck },
        { name: 'Epidemic Clusters', path: '/state/disease', icon: TrendingUp },
        { name: 'Emergency Escalation', path: '/state/emergency', icon: AlertTriangle, alert: true },
        { name: 'State Analytics', path: '/state/analytics', icon: BarChart3 },
        { name: 'State Alerts', path: '/state/alerts', icon: AlertTriangle },
      ],
    },
  ],

  DISTRICT_ADMIN: [
    {
      title: 'District Command',
      items: [
        { name: 'District Command', path: '/district/dashboard', icon: LayoutDashboard },
        { name: 'District Resource Map', path: '/district/map', icon: Map, badge: 'Local GPS' },
        { name: 'District Facilities', path: '/district/facilities', icon: Building2 },
      ],
    },
    {
      title: 'District Resources',
      items: [
        { name: 'District Inventory', path: '/district/inventory', icon: Package },
        { name: 'District Bed Matrix', path: '/district/beds', icon: Bed },
        { name: 'Personnel & Attendance', path: '/district/workforce', icon: Users },
      ],
    },
    {
      title: 'Triage & Crisis',
      items: [
        { name: 'Patient Waiting Queue', path: '/district/patients', icon: UserCheck },
        { name: 'Disease Surveillance', path: '/district/disease', icon: TrendingUp },
        { name: 'Emergency Mobilization', path: '/district/emergency', icon: AlertTriangle, alert: true },
        { name: 'District Analytics', path: '/district/analytics', icon: BarChart3 },
        { name: 'District Incident Alerts', path: '/district/alerts', icon: AlertTriangle },
      ],
    },
  ],

  FACILITY_ADMIN: [
    {
      title: 'Shared Operational Tools',
      items: [
        { name: 'Facility Directory', path: '/facilities', icon: Building2 },
        { name: 'Resource Map', path: '/map', icon: Map },
        { name: 'Supply Chain', path: '/warehouses', icon: Truck },
        { name: 'Reports & Analytics', path: '/analytics', icon: BarChart3 },
      ],
    },
    {
      title: 'Facility Operations',
      items: [
        { name: 'Facility Dashboard', path: '/facility/dashboard', icon: LayoutDashboard },
        { name: 'Medicine Stock', path: '/facility/stock', icon: Package },
        { name: 'Expiry Tracking (FEFO)', path: '/facility/expiry', icon: Clock },
        { name: 'Bed Availability', path: '/facility/beds', icon: Bed },
      ],
    },
    {
      title: 'Clinical Care & Assets',
      items: [
        { name: 'Staff Rosters', path: '/facility/workforce', icon: Users },
        { name: 'Daily Attendance', path: '/facility/attendance', icon: UserCheck },
        { name: 'Patient Footfall', path: '/facility/patients', icon: UserCheck },
        { name: 'Biomed Equipment', path: '/facility/equipment', icon: Wrench },
        { name: 'Ambulance Unit', path: '/facility/ambulance', icon: Truck },
      ],
    },
    {
      title: 'Alerts & Profile',
      items: [
        { name: 'Facility Alerts', path: '/facility/alerts', icon: AlertTriangle },
        { name: 'Facility Profile', path: '/facility/profile', icon: UserIcon },
      ],
    },
  ],
};
