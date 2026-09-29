import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  Sliders,
  Filter,
  Plus,
  Trash2,
  Send,
  Radio,
  Flame,
  Clock,
  Building2,
  ShieldAlert,
} from 'lucide-react';
import { useToast } from '@/hooks/useToast';

interface SystemAlert {
  id: string;
  facility: string;
  district: string;
  state: string;
  severity: 'critical' | 'high' | 'moderate' | 'info';
  category: 'Stock' | 'ICU' | 'Disease' | 'Equipment' | 'Staff';
  title: string;
  description: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
  autoEscalated: boolean;
}

interface ThresholdRule {
  id: string;
  metric: string;
  operator: '>' | '<' | '==';
  value: number;
  unit: string;
  severity: 'critical' | 'high' | 'moderate';
  channel: string;
  active: boolean;
}

const initialAlerts: SystemAlert[] = [
  {
    id: 'ALT-1092',
    facility: 'Patna District Civil Hospital',
    district: 'Patna',
    state: 'Bihar',
    severity: 'critical',
    category: 'Stock',
    title: 'Severe Insulin Stock-out Horizon (< 48 hrs)',
    description: 'Current batch consumption rate surged by 38% due to seasonal influx. Lead time from central depot is 5 days.',
    timestamp: '8 minutes ago',
    acknowledged: false,
    autoEscalated: true,
  },
  {
    id: 'ALT-1091',
    facility: 'AIIMS New Delhi Trauma Center',
    district: 'New Delhi',
    state: 'Delhi',
    severity: 'critical',
    category: 'ICU',
    title: 'ICU Bed Surge Overcapacity (98.4%)',
    description: 'Only 2 ventilators remaining in emergency isolation ward. Surge diversion protocol triggered.',
    timestamp: '22 minutes ago',
    acknowledged: true,
    acknowledgedBy: 'Dr. R. K. Sharma (MS)',
    autoEscalated: false,
  },
  {
    id: 'ALT-1089',
    facility: 'Siliguri District Hospital',
    district: 'Darjeeling',
    state: 'West Bengal',
    severity: 'high',
    category: 'Disease',
    title: 'Acute Respiratory Outbreak Cluster (R0 = 2.4)',
    description: 'Symptomatic triage reporting 145 cases in past 24 hours. Automated alert dispatched to State Surveillance Unit.',
    timestamp: '1 hour ago',
    acknowledged: false,
    autoEscalated: true,
  },
  {
    id: 'ALT-1087',
    facility: 'Guwahati Medical College & Hospital',
    district: 'Kamrup Metro',
    state: 'Assam',
    severity: 'high',
    category: 'Equipment',
    title: 'PSA Oxygen Plant Line Pressure Drop (3.4 bar)',
    description: 'Secondary compressor unit tripped on thermal overload. Backup liquid medical oxygen (LMO) tank engaged.',
    timestamp: '3 hours ago',
    acknowledged: true,
    acknowledgedBy: 'Eng. B. Borah (BioMed Lead)',
    autoEscalated: false,
  },
  {
    id: 'ALT-1084',
    facility: 'Dharavi Urban Health Center',
    district: 'Mumbai',
    state: 'Maharashtra',
    severity: 'moderate',
    category: 'Staff',
    title: 'Physician Shift Attendance Deficit (-3 Doctors)',
    description: 'Night duty roster unfulfilled due to seasonal illness. Temporary locum doctor requisition pending.',
    timestamp: '5 hours ago',
    acknowledged: false,
    autoEscalated: false,
  },
  {
    id: 'ALT-1079',
    facility: 'National Health Grid Mesh',
    district: 'National Node',
    state: 'Central',
    severity: 'info',
    category: 'Stock',
    title: 'Global Federated Round #42 Weight Convergence Complete',
    description: 'Federated demand optimization weights synchronized across 48 tier-1 hospital edge compute nodes.',
    timestamp: '7 hours ago',
    acknowledged: true,
    acknowledgedBy: 'System AI Daemon',
    autoEscalated: false,
  },
];

const initialRules: ThresholdRule[] = [
  {
    id: 'RUL-01',
    metric: 'Medicine Days-of-Inventory (DOI)',
    operator: '<',
    value: 5,
    unit: 'days',
    severity: 'critical',
    channel: 'SMS, WhatsApp & Incident Desk',
    active: true,
  },
  {
    id: 'RUL-02',
    metric: 'ICU Bed Occupancy Rate',
    operator: '>',
    value: 90,
    unit: '%',
    severity: 'critical',
    channel: 'Direct Emergency Callout + Siren',
    active: true,
  },
  {
    id: 'RUL-03',
    metric: 'Disease Cluster Growth Rate (Rt)',
    operator: '>',
    value: 1.8,
    unit: 'index',
    severity: 'high',
    channel: 'State Epidemiologist Digest & Email',
    active: true,
  },
  {
    id: 'RUL-04',
    metric: 'PSA Oxygen Generator Pressure',
    operator: '<',
    value: 4.2,
    unit: 'bar',
    severity: 'critical',
    channel: 'Biomedical Engineering Radio',
    active: true,
  },
  {
    id: 'RUL-05',
    metric: 'Doctor-to-Patient Ratio',
    operator: '>',
    value: 45,
    unit: 'pts/dr',
    severity: 'moderate',
    channel: 'Workforce Dispatcher App',
    active: true,
  },
];

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<SystemAlert[]>(initialAlerts);
  const [rules, setRules] = useState<ThresholdRule[]>(initialRules);
  const [activeTab, setActiveTab] = useState<'feed' | 'rules'>('feed');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [newRuleMetric, setNewRuleMetric] = useState('');
  const [newRuleValue, setNewRuleValue] = useState(85);
  const [newRuleSeverity, setNewRuleSeverity] = useState<'critical' | 'high' | 'moderate'>('high');
  const [newRuleChannel, setNewRuleChannel] = useState('SMS & Dashboard');

  const toast = useToast();

  const handleAcknowledge = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === id
          ? {
              ...a,
              acknowledged: true,
              acknowledgedBy: 'Current Officer (Simulated)',
            }
          : a
      )
    );
    toast.success(
      'Alert Acknowledged',
      `Incident ${id} marked as acknowledged by Command Desk.`
    );
  };

  const handleDismiss = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
    toast.info(
      'Alert Dismissed',
      `Incident ${id} removed from active dispatch queue.`
    );
  };

  const handleToggleRule = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    );
    toast.info(
      'Rule Status Updated',
      'Automated monitoring threshold state updated in engine.'
    );
  };

  const handleCreateRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleMetric.trim()) return;

    const newRule: ThresholdRule = {
      id: `RUL-0${rules.length + 1}`,
      metric: newRuleMetric,
      operator: '>',
      value: Number(newRuleValue),
      unit: '%',
      severity: newRuleSeverity,
      channel: newRuleChannel,
      active: true,
    };

    setRules([newRule, ...rules]);
    setIsRuleModalOpen(false);
    setNewRuleMetric('');
    toast.success(
      'Threshold Rule Activated',
      `Active trigger rule ${newRule.id} compiled into telemetry pipeline.`
    );
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false;
    if (categoryFilter !== 'all' && alert.category !== categoryFilter) return false;
    return true;
  });

  const criticalCount = alerts.filter((a) => a.severity === 'critical' && !a.acknowledged).length;
  const highCount = alerts.filter((a) => a.severity === 'high' && !a.acknowledged).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
              <Bell className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
                Emergency Alert Management & Threshold Rules
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Feature #58
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400">
                Push incident dispatch, automated triage escalation, and predictive telemetry threshold triggers.
              </p>
            </div>
          </div>
        </div>

        {/* Tab switch & Action */}
        <div className="flex items-center gap-2">
          <div className="flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setActiveTab('feed')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'feed'
                  ? 'bg-rose-500 text-white shadow-sm shadow-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Live Incident Feed ({alerts.length})
            </button>
            <button
              onClick={() => setActiveTab('rules')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'rules'
                  ? 'bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Threshold Engine ({rules.length})
            </button>
          </div>

          {activeTab === 'rules' && (
            <button
              onClick={() => setIsRuleModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500 text-slate-950 rounded-xl text-xs font-bold hover:bg-emerald-400 transition-colors shadow-sm shadow-emerald-500/20"
            >
              <Plus className="w-4 h-4" />
              New Rule
            </button>
          )}
        </div>
      </div>

      {/* KPI Severity Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/30 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">Unacknowledged Critical</span>
            <div className="text-2xl font-black text-rose-300 font-mono mt-1">{criticalCount}</div>
            <span className="text-[10px] text-slate-400">Require immediate intervention</span>
          </div>
          <AlertOctagon className="w-8 h-8 text-rose-500/40" />
        </div>

        <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">High Risk Alerts</span>
            <div className="text-2xl font-black text-amber-300 font-mono mt-1">{highCount}</div>
            <span className="text-[10px] text-slate-400">Escalating within 6 hrs</span>
          </div>
          <AlertTriangle className="w-8 h-8 text-amber-500/40" />
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-400">Automated Rules Active</span>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">{rules.filter((r) => r.active).length}</div>
            <span className="text-[10px] text-slate-400">Continuous micro-polling</span>
          </div>
          <Sliders className="w-8 h-8 text-teal-500/40" />
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">Dispatch Channels</span>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">4</div>
            <span className="text-[10px] text-slate-400">SMS, Radio, App, Webhook</span>
          </div>
          <Radio className="w-8 h-8 text-cyan-500/40" />
        </div>
      </div>

      {activeTab === 'feed' ? (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-bold text-slate-300">Filter By:</span>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical Only</option>
                <option value="high">High Only</option>
                <option value="moderate">Moderate Only</option>
                <option value="info">Info Only</option>
              </select>

              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="all">All Categories</option>
                <option value="Stock">Stock & Medicine</option>
                <option value="ICU">ICU & Bed Surge</option>
                <option value="Disease">Epidemic Outbreak</option>
                <option value="Equipment">Biomedical Equipment</option>
                <option value="Staff">Workforce & Staff</option>
              </select>
            </div>

            <div className="text-xs text-slate-400">
              Showing <span className="font-bold text-slate-200">{filteredAlerts.length}</span> active incidents
            </div>
          </div>

          {/* Incident Feed Cards */}
          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-2xl border transition-all ${
                  alert.severity === 'critical'
                    ? 'bg-rose-950/15 border-rose-500/40 hover:border-rose-500/60'
                    : alert.severity === 'high'
                    ? 'bg-amber-950/10 border-amber-500/30 hover:border-amber-500/50'
                    : alert.severity === 'moderate'
                    ? 'bg-blue-950/10 border-blue-500/30 hover:border-blue-500/50'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      {alert.severity === 'critical' ? (
                        <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                          <AlertOctagon className="w-5 h-5 animate-pulse" />
                        </div>
                      ) : alert.severity === 'high' ? (
                        <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                          <AlertTriangle className="w-5 h-5" />
                        </div>
                      ) : (
                        <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                          <Info className="w-5 h-5" />
                        </div>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-400">{alert.id}</span>
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                            alert.severity === 'critical'
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                              : alert.severity === 'high'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : alert.severity === 'moderate'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {alert.severity}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {alert.category}
                        </span>
                        {alert.autoEscalated && (
                          <span className="flex items-center gap-1 text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                            <Flame className="w-3 h-3" /> Auto-Escalated to State Command
                          </span>
                        )}
                      </div>

                      <h3 className="text-sm font-bold text-slate-100">{alert.title}</h3>
                      <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">{alert.description}</p>

                      <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3.5 h-3.5 text-slate-500" />
                          {alert.facility} ({alert.district}, {alert.state})
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {alert.timestamp}
                        </span>
                        {alert.acknowledged && (
                          <span className="flex items-center gap-1 text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Ack by {alert.acknowledgedBy}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    {!alert.acknowledged ? (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl transition-colors flex items-center gap-1.5 shadow-sm shadow-emerald-500/20"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Acknowledge
                      </button>
                    ) : (
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold">
                        Acknowledged
                      </span>
                    )}

                    <button
                      onClick={() => handleDismiss(alert.id)}
                      className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                      title="Dismiss from desk"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Threshold Rules Engine Tab */
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sliders className="w-6 h-6 text-emerald-400" />
              <div>
                <h3 className="text-sm font-bold text-slate-100">Automated Alert Triggers & Early Warning Rules</h3>
                <p className="text-xs text-slate-400">
                  When edge node telemetry violates threshold expressions, push notifications fire immediately.
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsRuleModalOpen(true)}
              className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-colors"
            >
              Add Threshold Rule
            </button>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">Rule ID</th>
                  <th className="py-3 px-4">Metric Tracked</th>
                  <th className="py-3 px-4">Condition</th>
                  <th className="py-3 px-4">Severity Level</th>
                  <th className="py-3 px-4">Dispatch Channel</th>
                  <th className="py-3 px-4">State</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-300">{rule.id}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-100">{rule.metric}</td>
                    <td className="py-3.5 px-4 font-mono text-emerald-400">
                      {rule.operator} {rule.value} {rule.unit}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          rule.severity === 'critical'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : rule.severity === 'high'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        }`}
                      >
                        {rule.severity}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">{rule.channel}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          rule.active
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-slate-800 text-slate-500'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${rule.active ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`} />
                        {rule.active ? 'Armed' : 'Disabled'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleToggleRule(rule.id)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-colors ${
                          rule.active
                            ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                            : 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40'
                        }`}
                      >
                        {rule.active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Rule Modal */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-emerald-400" />
                Configure New Threshold Trigger
              </h3>
              <button
                onClick={() => setIsRuleModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                  Metric Description
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ventilator Failure Rate, Dialysis Fluid Stock"
                  value={newRuleMetric}
                  onChange={(e) => setNewRuleMetric(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                    Threshold Value
                  </label>
                  <input
                    type="number"
                    required
                    value={newRuleValue}
                    onChange={(e) => setNewRuleValue(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                    Severity
                  </label>
                  <select
                    value={newRuleSeverity}
                    onChange={(e) => setNewRuleSeverity(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="moderate">Moderate</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                  Notification Channel
                </label>
                <input
                  type="text"
                  required
                  value={newRuleChannel}
                  onChange={(e) => setNewRuleChannel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRuleModalOpen(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold shadow-md shadow-emerald-500/20"
                >
                  Save & Arm Trigger
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsPage;
