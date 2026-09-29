import React, { useState } from 'react';
import { MOCK_FEDERATED_NODES, FederatedNode } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Cpu,
  ShieldCheck,
  Activity,
  Layers,
  RefreshCw,
  Server,
  Lock,
  Zap,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export const FederatedAIPage: React.FC = () => {
  const [nodes, setNodes] = useState<FederatedNode[]>(MOCK_FEDERATED_NODES);
  const [isAggregating, setIsAggregating] = useState(false);
  const toast = useToast();

  const roundAccuracyData = [
    { round: 'R38', accuracy: 89.2, loss: 0.34 },
    { round: 'R39', accuracy: 91.5, loss: 0.28 },
    { round: 'R40', accuracy: 93.8, loss: 0.21 },
    { round: 'R41', accuracy: 95.1, loss: 0.17 },
    { round: 'R42', accuracy: 96.8, loss: 0.12 },
  ];

  const handleTriggerRound = () => {
    setIsAggregating(true);
    setTimeout(() => {
      setIsAggregating(false);
      toast.success(
        'Federated Round #43 Initiated',
        'Dispatched global model weights to 4 connected hospital edge clusters via Flower coordinator.',
        5000
      );
    }, 1500);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30">
            <Cpu className="w-3.5 h-3.5" />
            <span>Privacy-Preserving Edge Mesh</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Federated AI Collaborative Learning Network
          </h2>
          <p className="text-xs text-slate-400">
            Decentralized machine learning training across hospital edge nodes without clinical EHR data leakage.
          </p>
        </div>

        <button
          onClick={handleTriggerRound}
          disabled={isAggregating}
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition-all hover:scale-105"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isAggregating ? 'animate-spin' : ''}`} />
          <span>{isAggregating ? 'Aggregating Gradients...' : 'Trigger Aggregation Round'}</span>
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Global Model Accuracy</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">96.8%</div>
          <span className="text-[11px] text-emerald-400 mt-2 block">+1.7% from Round 41</span>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Hospital Clusters</span>
            <Server className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">4 / 5 Online</div>
          <span className="text-[11px] text-slate-400 mt-2 block">1 offline (SMS Jaipur)</span>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Differential Privacy (ε)</span>
            <Lock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">ε = 0.95</div>
          <span className="text-[11px] text-purple-300 mt-2 block">Gaussian Noise Clipping Active</span>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Decentralized Records</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">463,900</div>
          <span className="text-[11px] text-cyan-300 mt-2 block">100% On-Premise Stored</span>
        </Card>
      </div>

      {/* Convergence Chart & Node List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Federated Convergence Curve (Accuracy vs Loss)
              </h3>
              <p className="text-[11px] text-slate-400">
                Flower FedAvg optimization rounds across multi-site clinical datasets
              </p>
            </div>
            <span className="text-xs font-mono text-teal-400">Round #42</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={roundAccuracyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="round" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[85, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#14b8a6"
                  strokeWidth={3}
                  dot={{ fill: '#14b8a6', r: 4 }}
                  name="Accuracy %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Participating Nodes List */}
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100">Edge Hospital Nodes</h3>
            <span className="text-[10px] text-slate-400 font-mono">Mesh Status</span>
          </div>

          <div className="space-y-2.5 overflow-y-auto max-h-72">
            {nodes.map((node) => (
              <div
                key={node.id}
                className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs text-slate-100">{node.facility_name}</span>
                  <span
                    className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded-full ${
                      node.status === 'online'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : node.status === 'training'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    {node.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 text-[10px] text-slate-400 font-mono">
                  <span>Samples: {node.local_samples.toLocaleString()}</span>
                  <span>Accuracy: {node.round_accuracy}%</span>
                  <span>Sync: {node.last_sync_time}</span>
                  <span>Epsilon: ε={node.privacy_epsilon}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default FederatedAIPage;
