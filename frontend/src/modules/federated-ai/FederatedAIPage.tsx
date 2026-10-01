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
  CheckCircle2,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

interface LocalNodeAccuracy {
  facility: string;
  localAccuracy: number;
  globalAccuracy: number;
  samplesTrained: number;
  epsilonSpent: number;
  lastSync: string;
  status: 'online' | 'offline' | 'training';
}

const localNodeAccuracies: LocalNodeAccuracy[] = [
  { facility: 'AIIMS New Delhi Trauma Edge Node', localAccuracy: 97.4, globalAccuracy: 96.8, samplesTrained: 42000, epsilonSpent: 1.8, lastSync: '3 mins ago', status: 'online' },
  { facility: 'Dr. RML Hospital Lucknow Node', localAccuracy: 95.8, globalAccuracy: 96.8, samplesTrained: 28400, epsilonSpent: 2.1, lastSync: '5 mins ago', status: 'online' },
  { facility: 'Patna Sadar Hospital Edge Cluster', localAccuracy: 94.2, globalAccuracy: 96.8, samplesTrained: 19800, epsilonSpent: 2.4, lastSync: '8 mins ago', status: 'online' },
  { facility: 'Varanasi District Hospital Node', localAccuracy: 96.1, globalAccuracy: 96.8, samplesTrained: 24500, epsilonSpent: 1.9, lastSync: '2 mins ago', status: 'online' },
  { facility: 'SMS Medical College Jaipur Node', localAccuracy: 91.5, globalAccuracy: 96.8, samplesTrained: 16000, epsilonSpent: 1.4, lastSync: '4 hours ago', status: 'offline' },
];

export const FederatedAIPage: React.FC = () => {
  const [nodes] = useState<FederatedNode[]>(MOCK_FEDERATED_NODES);
  const [isAggregating, setIsAggregating] = useState(false);
  const [currentRound, setCurrentRound] = useState(42);
  const [globalAccuracy, setGlobalAccuracy] = useState(96.8);
  const [lastSyncTime, setLastSyncTime] = useState('2 minutes ago');
  const toast = useToast();

  const activeNodesCount = localNodeAccuracies.filter((n) => n.status === 'online').length;
  const offlineNodesCount = localNodeAccuracies.filter((n) => n.status === 'offline').length;

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
      setCurrentRound((prev) => prev + 1);
      setGlobalAccuracy(97.2);
      setLastSyncTime('Just now');
      toast.success(
        `Federated Round #${currentRound + 1} Completed`,
        'Federated averaging (FedAvg) aggregated encrypted weight matrices from 4 active edge hospital nodes.',
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
            <span>Privacy-Preserving Edge Mesh • Flower FedAvg Framework</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Federated AI Collaborative Learning Network
          </h2>
          <p className="text-xs text-slate-400">
            Decentralized machine learning training across hospital edge nodes without clinical EHR data leakage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
            Last Sync: <strong className="text-slate-200">{lastSyncTime}</strong>
          </div>
          <button
            onClick={handleTriggerRound}
            disabled={isAggregating}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAggregating ? 'animate-spin' : ''}`} />
            <span>{isAggregating ? 'Aggregating Gradients...' : `Trigger Round #${currentRound + 1}`}</span>
          </button>
        </div>
      </div>

      {/* Phase 9 Metrics Grid (Active nodes, offline nodes, round, accuracy, privacy) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Current Training Round</span>
            <Sparkles className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">Round #{currentRound}</div>
          <p className="text-[11px] text-teal-400">FedAvg Convergence Reached</p>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Global Model Accuracy</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">{globalAccuracy}%</div>
          <p className="text-[11px] text-emerald-400">+1.7% from Round 41</p>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active vs Offline Nodes</span>
            <Server className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">
            <span className="text-emerald-400">{activeNodesCount} Online</span>{' '}
            <span className="text-slate-500 text-sm">/ {offlineNodesCount} Offline</span>
          </div>
          <p className="text-[11px] text-slate-400">1 node disconnected (SMS Jaipur)</p>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Privacy Budget Status (ε)</span>
            <Lock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-purple-400">ε = 2.4 / 10.0</div>
          <p className="text-[11px] text-purple-300">Differential Privacy (DP-SGD) Protected</p>
        </Card>
      </div>

      {/* Local Model Accuracy Comparison Table & Global Convergence Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Local vs Global Model Accuracy (Required by Phase 9) */}
        <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-3">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Local Model Accuracy vs Global Model</h3>
              <p className="text-[11px] text-slate-400">Individual edge node performance prior to aggregation.</p>
            </div>
            <span className="text-xs font-mono text-teal-400">5 Edge Nodes</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Hospital Edge Node</th>
                  <th className="py-2.5 px-3">Local Acc</th>
                  <th className="py-2.5 px-3">Global Acc</th>
                  <th className="py-2.5 px-3">Samples</th>
                  <th className="py-2.5 px-3">Last Sync</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {localNodeAccuracies.map((node) => (
                  <tr key={node.facility} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-200">{node.facility}</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-teal-400">{node.localAccuracy}%</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">{node.globalAccuracy}%</td>
                    <td className="py-2.5 px-3 font-mono text-slate-300">{node.samplesTrained.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-[11px] text-slate-400">{node.lastSync}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          node.status === 'online'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            node.status === 'online' ? 'bg-emerald-400' : 'bg-rose-400'
                          }`}
                        />
                        {node.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Global Convergence Curve */}
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Global Model Convergence Trajectory</h3>
              <p className="text-[11px] text-slate-400">Validation Accuracy (%) vs Categorical Cross-Entropy Loss</p>
            </div>
            <span className="text-xs font-mono text-emerald-400">Rounds 38-42</span>
          </div>

          <div className="h-60 w-full">
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
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#14b8a6"
                  strokeWidth={2.5}
                  name="Accuracy (%)"
                  dot={{ fill: '#14b8a6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Differential Privacy Guarantee Badge Section */}
      <Card className="p-4 bg-slate-900/90 border-slate-800 space-y-2">
        <div className="flex items-center gap-2">
          <Lock className="w-4 h-4 text-emerald-400" />
          <h3 className="text-xs font-bold text-slate-200">Zero Clinical EHR Data Egress Architecture</h3>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Sanjeevani Grid uses differential privacy stochastic gradient descent (DP-SGD) with Gaussian noise injection (σ=1.2) and gradient clipping threshold (C=1.0). Only mathematical weight deltas travel across the mesh; patient records and diagnostic reports never leave the originating hospital server.
        </p>
      </Card>
    </div>
  );
};

export default FederatedAIPage;
