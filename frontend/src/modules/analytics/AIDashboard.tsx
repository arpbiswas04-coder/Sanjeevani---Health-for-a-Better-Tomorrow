import React, { useState } from 'react';
import { MOCK_TRENDS } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Sparkles,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Calendar,
  Layers,
  BrainCircuit,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export const AIDashboard: React.FC = () => {
  const [selectedHorizon, setSelectedHorizon] = useState('7d');

  const explainabilityCards = [
    {
      medicine: 'Insulin Regular (10mL)',
      facility: 'RML Hospital Lucknow',
      stockoutDays: 5,
      riskPct: 91,
      confidence: 0.94,
      reasons: [
        'Local outpatient diabetic surge increased consumption by +27%',
        'Current on-hand inventory covers only 4.8 days of runway',
        'State supplier procurement lead time is 8 days',
      ],
    },
    {
      medicine: 'Liquid Medical Oxygen (Type-D)',
      facility: 'Patna Sadar Hospital',
      stockoutDays: 2,
      riskPct: 94,
      confidence: 0.98,
      reasons: [
        'Severe acute respiratory influx (+45% weekly spike)',
        'Cylinder buffer reserve at critical 9 hours buffer',
        'High highway transit congestion predicted on NH-31',
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
            Predictive Health Resource & Demand Forecasting
          </h2>
          <p className="text-xs text-slate-400">
            Ensemble time-series projections with transparent SHAP feature attribution.
          </p>
        </div>

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
      </div>

      {/* Main Forecast Graph */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              Projected Medicine Consumption vs Available Supply ({selectedHorizon})
            </h3>
            <p className="text-[11px] text-slate-400">
              Confidence Band (95% CI) based on LightGBM + Prophet lag predictors
            </p>
          </div>
          <Badge level="low">94.8% Backtest Accuracy</Badge>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={MOCK_TRENDS}>
              <defs>
                <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorSupply" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#f8fafc',
                }}
              />
              <Area
                type="monotone"
                dataKey="demand"
                stroke="#10b981"
                fillOpacity={1}
                fill="url(#colorDemand)"
                strokeWidth={2}
                name="Projected Demand"
              />
              <Area
                type="monotone"
                dataKey="supply"
                stroke="#06b6d4"
                fillOpacity={1}
                fill="url(#colorSupply)"
                strokeWidth={2}
                name="Available Supply"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* AI Explainability Cards */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Transparent AI Explainability Cards (Member 3 Prediction Contracts)
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {explainabilityCards.map((card) => (
            <Card key={card.medicine} className="flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-2.5">
                  <div>
                    <h4 className="font-bold text-xs text-slate-100">{card.medicine}</h4>
                    <span className="text-[10px] text-slate-400">{card.facility}</span>
                  </div>
                  <Badge level={card.riskPct > 90 ? 'critical' : 'high'}>
                    {card.riskPct}% Risk
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-3 font-mono">
                  <div className="p-2 bg-slate-950/70 rounded-lg">
                    <span className="text-[10px] text-slate-500 block">Stockout Horizon</span>
                    <strong className="text-rose-400">{card.stockoutDays} days</strong>
                  </div>
                  <div className="p-2 bg-slate-950/70 rounded-lg">
                    <span className="text-[10px] text-slate-500 block">AI Confidence</span>
                    <strong className="text-emerald-400">{(card.confidence * 100).toFixed(0)}%</strong>
                  </div>
                </div>

                <div className="mt-3 space-y-1.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                    Attribution Drivers:
                  </span>
                  <ul className="space-y-1 text-[11px] text-slate-300">
                    {card.reasons.map((r, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-400 font-bold">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                <span>Model: LightGBM-v2</span>
                <span className="text-teal-400 font-mono">Auto-Tuned</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AIDashboard;
