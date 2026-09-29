import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useHealth } from '@/hooks/useHealth';
import { ShieldCheck, Server, Cpu, Network } from 'lucide-react';

export const HomePage: React.FC = () => {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-10">
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck className="w-4 h-4" />
          Production-Ready Monorepo Architecture
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
          Sanjeevani Grid
        </h1>
        <p className="text-lg text-slate-300 font-medium">
          Health Resource Intelligence Platform
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <Server className="w-4 h-4 text-emerald-400" />
                Backend API Status
              </span>
              {isLoading && <Badge level="info">Checking...</Badge>}
              {isError && <Badge level="critical">Offline / Connecting</Badge>}
              {health && <Badge level="success">Healthy</Badge>}
            </div>
            <p className="text-xs text-slate-400">
              Connected to FastAPI service with PostgreSQL and Redis orchestration.
            </p>
          </div>
          <div className="mt-4 p-3 bg-slate-900/80 rounded-lg text-xs font-mono text-slate-300">
            {health ? (
              <pre>{JSON.stringify(health, null, 2)}</pre>
            ) : (
              <span className="text-slate-500">Connecting to /api/v1/health...</span>
            )}
          </div>
        </Card>

        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <Network className="w-4 h-4 text-teal-400" />
                Monorepo Workstreams
              </span>
              <Badge level="low">4 Independent Tracks</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Each team member operates in dedicated branches with isolated module trees.
            </p>
          </div>
          <ul className="mt-4 space-y-1.5 text-xs text-slate-300">
            <li className="flex items-center justify-between">
              <span>Member 1: Frontend SPA</span>
              <span className="font-mono text-emerald-400 text-[11px]">frontend/member-1</span>
            </li>
            <li className="flex items-center justify-between">
              <span>Member 2: Backend Core & DB</span>
              <span className="font-mono text-emerald-400 text-[11px]">backend/member-2</span>
            </li>
            <li className="flex items-center justify-between">
              <span>Member 3: AI Models & Forecasts</span>
              <span className="font-mono text-emerald-400 text-[11px]">ai/member-3</span>
            </li>
            <li className="flex items-center justify-between">
              <span>Member 4: Infra, Federated & Opt</span>
              <span className="font-mono text-emerald-400 text-[11px]">infra/member-4</span>
            </li>
          </ul>
        </Card>
      </div>

      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>Federated Learning & Google OR-Tools optimization modules ready for integration.</span>
        </div>
        <span className="font-mono text-slate-500">develop &rarr; main</span>
      </div>
    </div>
  );
};
