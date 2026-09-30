import React, { useState } from 'react';
import { MOCK_TRENDS } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Sparkles,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Calendar,
  Layers,
  BrainCircuit,
  BarChart3,
  DollarSign,
  ShieldCheck,
  TrendingDown,
  Activity,
  Bed,
  Package,
  Users,
  Clock,
  ArrowRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

export const AIDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'forecasting' | 'trends' | 'cost' | 'resilience' | 'comparison'>('forecasting');
  const [selectedHorizon, setSelectedHorizon] = useState('7d');
  const toast = useToast();

  const explainabilityCards = [
    {
      medicine: 'Insulin Regular (10mL)',
      facility: 'RML Hospital Lucknow',
      stockoutDays: 5,
      riskPct: 91,
      confidence: 0.94,
      reasons: [
        'Demand increased 27% in recent OPD wave',
        'Current stock covers only 4.8 days of runway',
        'Supplier lead time is 8 days',
      ],
    },
    {
      medicine: 'Liquid Medical Oxygen (Type-D)',
      facility: 'Patna Sadar Hospital',
      stockoutDays: 2,
      riskPct: 94,
      confidence: 0.98,
      reasons: [
        'Acute respiratory influx (+45% weekly spike)',
        'Current stock covers only 9 hours of emergency reserves',
        'Supplier highway transit congestion on NH-31',
      ],
    },
    {
      medicine: 'Paracetamol IV Infusion',
      facility: 'PHC Malihabad',
      stockoutDays: 6,
      riskPct: 88,
      confidence: 0.89,
      reasons: [
        'Seasonal Dengue cluster identified across 4 nearby villages',
        'Reorder threshold breached 48 hours ago',
      ],
    },
  ];

  const historicalTrendsData = [
    { month: 'Jan', consumption: 14200, bedUtil: 78, wastage: 84000 },
    { month: 'Feb', consumption: 15100, bedUtil: 75, wastage: 76000 },
    { month: 'Mar', consumption: 16800, bedUtil: 79, wastage: 69000 },
    { month: 'Apr', consumption: 19400, bedUtil: 84, wastage: 58000 },
    { month: 'May', consumption: 23100, bedUtil: 88, wastage: 51000 },
    { month: 'Jun', consumption: 21500, bedUtil: 85, wastage: 44000 },
    { month: 'Jul', consumption: 26800, bedUtil: 91, wastage: 38000 },
    { month: 'Aug', consumption: 28400, bedUtil: 92, wastage: 32000 },
    { month: 'Sep', consumption: 27100, bedUtil: 86, wastage: 29000 },
  ];

  const districtComparisonData = [
    { district: 'Lucknow', resilience: 92, bedOccupancy: 84, avgEta: 8.2, stockouts: 1 },
    { district: 'Kanpur', resilience: 88, bedOccupancy: 79, avgEta: 9.1, stockouts: 2 },
    { district: 'Varanasi', resilience: 85, bedOccupancy: 74, avgEta: 11.4, stockouts: 2 },
    { district: 'Patna', resilience: 74, bedOccupancy: 91, avgEta: 14.2, stockouts: 6 },
    { district: 'Gorakhpur', resilience: 79, bedOccupancy: 86, avgEta: 12.8, stockouts: 4 },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <BrainCircuit className="w-3.5 h-3.5" />
            <span>Machine Learning Intelligence & Explainability</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Analytics, Predictive AI & Supply Chain Resilience
          </h2>
          <p className="text-xs text-slate-400">
            Demand forecasting, historical utilization curves, cost-benefit wastage analytics, and district benchmarking.
          </p>
        </div>

        {/* Horizon Filter for Forecast */}
        {activeTab === 'forecasting' && (
          <div className="flex items-center gap-2 bg-slate-900 p-1 border border-slate-800 rounded-xl">
            {['24h', '7d', '14d', '30d'].map((h) => (
              <button
                key={h}
                onClick={() => setSelectedHorizon(h)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                  selectedHorizon === h
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {h} Horizon
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Tabs Group */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { key: 'forecasting', label: 'AI Demand & Capacity Forecast (Phase 7)', icon: Sparkles },
          { key: 'trends', label: 'Historical Trend & Utilization (Features 63-64)', icon: Activity },
          { key: 'cost', label: 'Cost & Wastage Reduction (Features 65-66)', icon: DollarSign },
          { key: 'resilience', label: 'Resilience & Risk Scores (Features 67-68)', icon: ShieldCheck },
          { key: 'comparison', label: 'District Comparison & Benchmarking (Features 69-70)', icon: BarChart3 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: Phase 7 AI UI (Demand, Stockout, Bed, Patient, Workforce, Explainability) */}
      {activeTab === 'forecasting' && (
        <div className="space-y-6">
          {/* Phase 7 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Stock-out Probability</span>
              <div className="text-2xl font-bold font-mono text-rose-400">91% Risk</div>
              <p className="text-[11px] text-rose-400">Insulin at RML Hospital (5 days)</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Bed Forecast (7-Day Projection)</span>
              <div className="text-2xl font-bold font-mono text-amber-400">+14% Occupancy</div>
              <p className="text-[11px] text-amber-300">Respiratory surge expected next week</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Patient Forecast</span>
              <div className="text-2xl font-bold font-mono text-cyan-400">48,200 Admissions</div>
              <p className="text-[11px] text-cyan-300">Confidence Score: 0.94</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Workforce Fatigue Index</span>
              <div className="text-2xl font-bold font-mono text-purple-400">Moderate (1:22)</div>
              <p className="text-[11px] text-purple-300">Rota reallocation suggested for ICU</p>
            </Card>
          </div>

          {/* Forecast Area Graph */}
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100">Projected Demand vs Historical Consumption</h3>
                <p className="text-[11px] text-slate-400">
                  Ensemble time-series forecast (Prophet + XGBoost) with 95% confidence interval
                </p>
              </div>
              <Badge level="low">Confidence: 94.2%</Badge>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={MOCK_TRENDS}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Area type="monotone" dataKey="actual" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.1} name="Actual Dispensation" />
                  <Area type="monotone" dataKey="forecast" stroke="#10b981" fill="#10b981" fillOpacity={0.2} name="AI Predicted Demand" strokeDasharray="4 4" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Explainability Panel (Phase 7 Blueprint Spec) */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-slate-100">SHAP AI Feature Attribution & Explainability Panel</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {explainabilityCards.map((card) => (
                <Card key={card.medicine} className="space-y-3 border-l-4 border-l-rose-500">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-xs text-slate-100">{card.medicine}</h4>
                      <span className="text-[10px] text-slate-400">{card.facility}</span>
                    </div>
                    <Badge level={card.riskPct > 90 ? 'critical' : 'high'}>{card.riskPct}% Risk</Badge>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl space-y-1 font-mono text-xs">
                    <div className="text-rose-400 font-bold">Predicted stock-out: {card.stockoutDays} days</div>
                    <div className="text-cyan-400 text-[11px]">Confidence: {(card.confidence * 100).toFixed(0)}%</div>
                  </div>

                  <div className="space-y-1 pt-1">
                    <span className="text-[11px] font-semibold text-slate-300 block">Identified Causal Drivers:</span>
                    <ul className="space-y-1">
                      {card.reasons.map((r, idx) => (
                        <li key={idx} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                          <span className="text-rose-400">•</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Historical Trend Analysis & Resource Utilization (Features 63 & 64) */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100">9-Month Healthcare Resource Consumption & Bed Utilization</h3>
                <p className="text-[11px] text-slate-400">Monthly medical supplies volume vs inpatient bed occupancy %</p>
              </div>
              <span className="text-xs font-mono text-emerald-400">Multi-District Telemetry</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={historicalTrendsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="consumption" fill="#06b6d4" name="Monthly Units Dispensed" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="bedUtil" fill="#a855f7" name="Bed Occupancy %" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">ICU Bed Turnover Rate</span>
              <div className="text-2xl font-bold font-mono text-slate-100">3.8 Days ALOS</div>
              <p className="text-[11px] text-emerald-400">-0.6 days vs benchmark</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Ventilator Telemetry Uptime</span>
              <div className="text-2xl font-bold font-mono text-emerald-400">99.2%</div>
              <p className="text-[11px] text-slate-400">140 hours mean time between failure</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Ambulance Fleet Response</span>
              <div className="text-2xl font-bold font-mono text-cyan-400">8.8 Mins Avg</div>
              <p className="text-[11px] text-emerald-400">22% faster via green corridor routing</p>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 3: Cost Analytics & Wastage Reduction Dashboard (Features 65 & 66) */}
      {activeTab === 'cost' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Total Wastage Prevented (YTD)</span>
              <div className="text-2xl font-bold font-mono text-emerald-400">₹42.8 Lakhs</div>
              <p className="text-[11px] text-emerald-400">Via algorithmic FEFO redistribution</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Emergency Spot-Purchase Savings</span>
              <div className="text-2xl font-bold font-mono text-teal-400">₹18.4 Lakhs</div>
              <p className="text-[11px] text-teal-300">Avoided panic spot premiums</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Expired Drug Loss Reduction</span>
              <div className="text-2xl font-bold font-mono text-purple-400">-64.2%</div>
              <p className="text-[11px] text-slate-400">From 4.8% to 1.7% total volume</p>
            </Card>
          </div>

          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100">Monthly Wastage Reduction Trajectory (₹ INR)</h3>
                <p className="text-[11px] text-slate-400">Losses reduced steadily since Sanjeevani Grid automated rebalancing rollout.</p>
              </div>
              <span className="text-xs font-mono text-emerald-400">Continuous Improvement</span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalTrendsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Area type="monotone" dataKey="wastage" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} name="Monthly Loss Value (₹)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: Supply Chain Resilience Score UI & Health Resource Risk Score UI (Features 67 & 68) */}
      {activeTab === 'resilience' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-sm font-bold text-slate-100">Supply Chain Resilience Score Breakdown</h3>
                </div>
                <span className="text-base font-black font-mono text-emerald-400">94.8 / 100</span>
              </div>

              <div className="space-y-3 text-xs">
                {[
                  { name: 'Buffer Stock Adequacy (Days of Cover)', score: 96, weight: '35%' },
                  { name: 'Cold-Chain Telemetry Reliability', score: 98, weight: '25%' },
                  { name: 'Supplier Diversity & Redundancy', score: 88, weight: '20%' },
                  { name: 'Inter-Facility Transit Speed & Corridors', score: 92, weight: '20%' },
                ].map((item) => (
                  <div key={item.name} className="space-y-1">
                    <div className="flex justify-between text-slate-300">
                      <span>{item.name} <span className="text-slate-500 font-mono">({item.weight})</span></span>
                      <strong className="font-mono text-emerald-400">{item.score}%</strong>
                    </div>
                    <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${item.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5 bg-slate-900 border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                  <h3 className="text-sm font-bold text-slate-100">Health Resource Risk Score (By District)</h3>
                </div>
                <span className="text-xs text-slate-400">Lower = Safer</span>
              </div>

              <div className="space-y-3 text-xs">
                {[
                  { district: 'Patna District', risk: 62, level: 'high' as const, alert: 'Oxygen reserve buffer narrow' },
                  { district: 'Gorakhpur District', risk: 48, level: 'moderate' as const, alert: 'Seasonal pediatric demand' },
                  { district: 'Lucknow District', risk: 28, level: 'low' as const, alert: 'Depot stock healthy' },
                  { district: 'Delhi Central', risk: 18, level: 'low' as const, alert: 'Optimal buffer reserves' },
                ].map((item) => (
                  <div key={item.district} className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="font-bold text-slate-100">{item.district}</div>
                      <div className="text-[10px] text-slate-400">{item.alert}</div>
                    </div>
                    <div className="text-right">
                      <Badge level={item.level}>{item.risk} Risk Pts</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 5: District Comparison & Performance Dashboard (Features 69 & 70) */}
      {activeTab === 'comparison' && (
        <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-3">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Inter-District Health Grid Performance Scorecard</h3>
              <p className="text-[11px] text-slate-400">Benchmarking across bed availability, supply chain resilience, ambulance response, and stockout incidents.</p>
            </div>
            <span className="text-xs font-mono text-emerald-400">5 Districts Benchmarked</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">District Hub</th>
                  <th className="py-3 px-4">Resilience Index</th>
                  <th className="py-3 px-4">Bed Occupancy %</th>
                  <th className="py-3 px-4">Ambulance ETA</th>
                  <th className="py-3 px-4">Stockout Incidents (30d)</th>
                  <th className="py-3 px-4">Overall Performance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {districtComparisonData.map((d) => (
                  <tr key={d.district} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-100">{d.district}</td>
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400">{d.resilience} / 100</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{d.bedOccupancy}%</td>
                    <td className="py-3 px-4 font-mono text-cyan-400">{d.avgEta} mins</td>
                    <td className="py-3 px-4 font-mono">
                      <span className={d.stockouts > 3 ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                        {d.stockouts} incidents
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Badge level={d.resilience > 85 ? 'low' : d.resilience > 75 ? 'moderate' : 'high'}>
                        {d.resilience > 85 ? 'TIER 1 (EXCELLENT)' : d.resilience > 75 ? 'TIER 2 (STABLE)' : 'TIER 3 (NEEDS BUFFER)'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default AIDashboard;
