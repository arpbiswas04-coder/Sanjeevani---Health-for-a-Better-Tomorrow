import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Building2,
  Package,
  Truck,
  ThermometerSnowflake,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  CheckCircle2,
  AlertTriangle,
  Boxes,
  Search,
  RefreshCw,
  Send,
  ShieldCheck,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface WarehouseHub {
  id: string;
  name: string;
  location: string;
  state: string;
  totalCapacityPallets: number;
  utilizedPallets: number;
  coldChainCapacityLiters: number;
  coldChainUtilizedPct: number;
  activeDispatchesToday: number;
  inboundShipmentsPending: number;
  status: 'optimal' | 'moderate' | 'near-capacity';
}

const mockWarehouses: WarehouseHub[] = [
  {
    id: 'WH-UP-01',
    name: 'State Central Medical Store Depot (CMSD) Lucknow',
    location: 'Transport Nagar, Lucknow',
    state: 'Uttar Pradesh',
    totalCapacityPallets: 12500,
    utilizedPallets: 10450,
    coldChainCapacityLiters: 45000,
    coldChainUtilizedPct: 82.5,
    activeDispatchesToday: 38,
    inboundShipmentsPending: 6,
    status: 'moderate',
  },
  {
    id: 'WH-BR-01',
    name: 'Bihar State Health Logistics Hub Patna',
    location: 'Fatuha Industrial Area, Patna',
    state: 'Bihar',
    totalCapacityPallets: 9800,
    utilizedPallets: 8900,
    coldChainCapacityLiters: 32000,
    coldChainUtilizedPct: 91.2,
    activeDispatchesToday: 42,
    inboundShipmentsPending: 9,
    status: 'near-capacity',
  },
  {
    id: 'WH-DL-01',
    name: 'National Strategic Health Stockpile Hub New Delhi',
    location: 'Okhla Phase-II, New Delhi',
    state: 'Delhi',
    totalCapacityPallets: 28000,
    utilizedPallets: 18200,
    coldChainCapacityLiters: 120000,
    coldChainUtilizedPct: 65.0,
    activeDispatchesToday: 64,
    inboundShipmentsPending: 12,
    status: 'optimal',
  },
  {
    id: 'WH-RJ-01',
    name: 'Rajasthan Medical Services Corporation Central Depot',
    location: 'Sitapura Industrial Area, Jaipur',
    state: 'Rajasthan',
    totalCapacityPallets: 11000,
    utilizedPallets: 8400,
    coldChainCapacityLiters: 38000,
    coldChainUtilizedPct: 76.4,
    activeDispatchesToday: 29,
    inboundShipmentsPending: 4,
    status: 'optimal',
  },
];

const dispatchQueue = [
  {
    id: 'DSP-8821',
    warehouse: 'CMSD Lucknow',
    destination: 'Kanpur District Civil Hospital',
    asset: 'Liquid Medical Oxygen (Type-D Cylinders)',
    quantity: '180 Cylinders',
    status: 'En Route (GPS Tracking Active)',
    eta: '42 mins',
    driver: 'Convoy Lead Rajesh Verma',
  },
  {
    id: 'DSP-8822',
    warehouse: 'Patna Logistics Hub',
    destination: 'Muzaffarpur Sadar Hospital',
    asset: 'Pediatric IV Paracetamol & Antibiotics',
    quantity: '4,500 Vials',
    status: 'Loading at Bay 3',
    eta: '2.5 hours',
    driver: 'Driver S. K. Yadav',
  },
  {
    id: 'DSP-8823',
    warehouse: 'Delhi Strategic Hub',
    destination: 'Agra Medical College',
    asset: 'Anti-Rabies Vaccines (2-8°C Cold Chain)',
    quantity: '2,000 Doses',
    status: 'Departed Gateway',
    eta: '3.1 hours',
    driver: 'Express Courier Reefer-09',
  },
];

export const WarehouseDashboardPage: React.FC = () => {
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>('WH-UP-01');
  const [search, setSearch] = useState('');
  const toast = useToast();

  const selectedWarehouse =
    mockWarehouses.find((w) => w.id === selectedWarehouseId) || mockWarehouses[0];

  const chartData = mockWarehouses.map((w) => ({
    name: w.name.split(' ')[0] + ' ' + w.state,
    utilized: Math.round((w.utilizedPallets / w.totalCapacityPallets) * 100),
    coldChain: Math.round(w.coldChainUtilizedPct),
  }));

  const handleDispatchRebalance = () => {
    toast.success(
      'Automated Cross-Docking Authorized',
      `Rebalanced 1,200 units from ${selectedWarehouse.name} to buffer high-demand PHCs. Route generated.`
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Boxes className="w-3.5 h-3.5" />
            <span>State Medical Store Depots & Central Logistics Hubs</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Warehouse Network & Cold-Chain Capacity Dashboard
          </h2>
          <p className="text-xs text-slate-400">
            Bulk pharmaceutical warehousing, temperature-controlled vaccine stockpiles, and fleet dispatch queues.
          </p>
        </div>

        <button
          onClick={handleDispatchRebalance}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:scale-105 active:scale-95"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Trigger Automated Rebalancing</span>
        </button>
      </div>

      {/* Aggregate KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Pallet Capacity</span>
            <Boxes className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">61,300</div>
          <div className="text-[11px] text-slate-400">74.9% Net Network Utilization</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Cold-Chain Volume</span>
            <ThermometerSnowflake className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">235,000 L</div>
          <div className="text-[11px] text-cyan-400">Active temperature logging (2-8°C)</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Dispatches Today</span>
            <Truck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">173 Convoys</div>
          <div className="text-[11px] text-emerald-400">98.4% On-Time Delivery ETA</div>
        </Card>

        <Card className="p-4 bg-slate-900 border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Pending Inbound Shipments</span>
            <ArrowDownLeft className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">31 Tranches</div>
          <div className="text-[11px] text-slate-400">From verified GMP manufacturers</div>
        </Card>
      </div>

      {/* Warehouse Selector & Detailed Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hub List */}
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100">Strategic Warehouses</h3>
            <span className="text-[11px] text-slate-400 font-mono">4 Nodes Online</span>
          </div>

          <div className="space-y-2.5">
            {mockWarehouses.map((wh) => {
              const utilPct = Math.round((wh.utilizedPallets / wh.totalCapacityPallets) * 100);
              const isSelected = wh.id === selectedWarehouseId;

              return (
                <button
                  key={wh.id}
                  onClick={() => setSelectedWarehouseId(wh.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    isSelected
                      ? 'bg-slate-800/90 border-emerald-500/60 shadow-md'
                      : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-semibold text-xs text-slate-200">{wh.name}</div>
                      <div className="text-[10px] text-slate-400">{wh.location}</div>
                    </div>
                    <Badge
                      level={wh.status === 'optimal' ? 'low' : wh.status === 'moderate' ? 'moderate' : 'high'}
                    >
                      {utilPct}% Full
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 font-mono">
                    <span>Pallets: {wh.utilizedPallets.toLocaleString()} / {wh.totalCapacityPallets.toLocaleString()}</span>
                    <span className="text-cyan-400">Cold: {wh.coldChainUtilizedPct}%</span>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>

        {/* Selected Hub Deep-Dive */}
        <Card className="lg:col-span-2 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h3 className="font-bold text-base text-slate-100">{selectedWarehouse.name}</h3>
              <p className="text-xs text-slate-400">
                {selectedWarehouse.location} • {selectedWarehouse.state}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-emerald-400">
                Hub ID: {selectedWarehouse.id}
              </span>
            </div>
          </div>

          {/* Capacity Progress Bars */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-medium">Dry Ambient Pallet Capacity</span>
                <span className="font-mono text-slate-100 font-bold">
                  {Math.round((selectedWarehouse.utilizedPallets / selectedWarehouse.totalCapacityPallets) * 100)}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.round(
                      (selectedWarehouse.utilizedPallets / selectedWarehouse.totalCapacityPallets) * 100
                    )}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{selectedWarehouse.utilizedPallets.toLocaleString()} occupied</span>
                <span>{(selectedWarehouse.totalCapacityPallets - selectedWarehouse.utilizedPallets).toLocaleString()} free</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-medium">Refrigerated Cold-Chain Buffer</span>
                <span className="font-mono text-cyan-400 font-bold">
                  {selectedWarehouse.coldChainUtilizedPct}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                  style={{ width: `${selectedWarehouse.coldChainUtilizedPct}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>{selectedWarehouse.coldChainCapacityLiters.toLocaleString()} Liters</span>
                <span>Dual Compressor Backup OK</span>
              </div>
            </div>
          </div>

          {/* Hub Comparison Chart */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 mb-2">Network Hub Capacity Utilization Comparison (%)</h4>
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="utilized" fill="#10b981" name="Dry Pallets %" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="coldChain" fill="#06b6d4" name="Cold-Chain %" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      </div>

      {/* Live Outbound Dispatch Logistics Queue */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Truck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-slate-100">Live Logistics & Redistribution Dispatch Queue</h3>
          </div>
          <span className="text-xs text-slate-400">GPS Telemetry Integrated</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Dispatch ID</th>
                <th className="py-2.5 px-3">Source Warehouse</th>
                <th className="py-2.5 px-3">Destination Facility</th>
                <th className="py-2.5 px-3">Consignment</th>
                <th className="py-2.5 px-3">Volume</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">ETA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-normal">
              {dispatchQueue.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3 font-mono font-bold text-slate-100">{item.id}</td>
                  <td className="py-2.5 px-3 text-slate-300">{item.warehouse}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">{item.destination}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{item.asset}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-100">{item.quantity}</td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      {item.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-amber-400 font-bold">{item.eta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default WarehouseDashboardPage;
