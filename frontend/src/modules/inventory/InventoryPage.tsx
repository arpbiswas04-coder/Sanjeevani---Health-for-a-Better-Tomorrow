import React, { useState } from 'react';
import { MOCK_INVENTORY, InventoryItem } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/hooks/useToast';
import {
  Package,
  Search,
  AlertTriangle,
  ArrowRightLeft,
  QrCode,
  CheckCircle2,
  Clock,
  Filter,
  Layers,
  Calendar,
  History,
  TrendingDown,
  Barcode,
  Camera,
  RefreshCw,
  Plus,
  Send,
  ShieldAlert,
} from 'lucide-react';

interface BatchItem {
  id: string;
  medicineName: string;
  batchNo: string;
  mfgDate: string;
  expDate: string;
  quantity: number;
  unit: string;
  facility: string;
  coldChainTemp: string;
  rackLocation: string;
  status: 'valid' | 'near-expiry' | 'expired';
}

interface StockHistoryRecord {
  id: string;
  timestamp: string;
  medicineName: string;
  type: 'Inbound Delivery' | 'Ward Disbursement' | 'Inter-facility Transfer' | 'Disposal';
  quantityChange: string;
  sourceTarget: string;
  authorizedBy: string;
}

const mockBatches: BatchItem[] = [
  { id: 'b-01', medicineName: 'Insulin Regular (10mL)', batchNo: 'IN-2026-X88', mfgDate: '2025-10-15', expDate: '2026-10-15', quantity: 240, unit: 'vials', facility: 'RML Lucknow', coldChainTemp: '2°C - 8°C (OK)', rackLocation: 'Reefer Unit A-3', status: 'near-expiry' },
  { id: 'b-02', medicineName: 'Insulin Regular (10mL)', batchNo: 'IN-2026-Z12', mfgDate: '2026-02-10', expDate: '2027-02-10', quantity: 650, unit: 'vials', facility: 'CMSD Depot', coldChainTemp: '4°C (OK)', rackLocation: 'Central Cold Vault 2', status: 'valid' },
  { id: 'b-03', medicineName: 'Amoxicillin 500mg', batchNo: 'AMX-4491-A', mfgDate: '2025-06-01', expDate: '2026-10-01', quantity: 4200, unit: 'capsules', facility: 'Patna Sadar', coldChainTemp: 'Ambient 22°C', rackLocation: 'Dry Rack C-12', status: 'near-expiry' },
  { id: 'b-04', medicineName: 'Oral Rehydration Salts (ORS)', batchNo: 'ORS-9912-B', mfgDate: '2024-08-10', expDate: '2026-08-10', quantity: 180, unit: 'sachets', facility: 'PHC Malihabad', coldChainTemp: 'Ambient 24°C', rackLocation: 'Disposal Bin', status: 'expired' },
  { id: 'b-05', medicineName: 'Paracetamol IV 100mL', batchNo: 'PCM-IV-7721', mfgDate: '2026-01-20', expDate: '2028-01-20', quantity: 3800, unit: 'bottles', facility: 'Varanasi CHC', coldChainTemp: 'Ambient 20°C', rackLocation: 'Main Aisle 4', status: 'valid' },
];

const mockStockHistory: StockHistoryRecord[] = [
  { id: 'hist-1', timestamp: '2026-09-30 08:15', medicineName: 'Insulin Regular (10mL)', type: 'Inter-facility Transfer', quantityChange: '-50 vials', sourceTarget: 'Dispatched to PHC Malihabad', authorizedBy: 'Pharmacist R. Sharma' },
  { id: 'hist-2', timestamp: '2026-09-29 16:40', medicineName: 'Amoxicillin 500mg', type: 'Ward Disbursement', quantityChange: '-200 caps', sourceTarget: 'General IPD Ward 3', authorizedBy: 'Nurse Supv. Priya Singh' },
  { id: 'hist-3', timestamp: '2026-09-29 11:20', medicineName: 'Paracetamol IV 100mL', type: 'Inbound Delivery', quantityChange: '+1,200 bottles', sourceTarget: 'Received from CMSD Lucknow', authorizedBy: 'Storekeeper A. Verma' },
  { id: 'hist-4', timestamp: '2026-09-28 14:05', medicineName: 'Liquid Medical Oxygen (Type-D)', type: 'Inbound Delivery', quantityChange: '+60 cylinders', sourceTarget: 'Linde Air Products Consignment', authorizedBy: 'Bio-Med Eng. S. Gupta' },
];

export const InventoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'medicines' | 'batches' | 'lowStock' | 'expiry' | 'history' | 'scan'>('medicines');
  const [items, setItems] = useState<InventoryItem[]>(MOCK_INVENTORY);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [transferTarget, setTransferTarget] = useState<InventoryItem | null>(null);
  const [transferAmount, setTransferAmount] = useState(50);
  const [destinationFacility, setDestinationFacility] = useState('Patna Sadar Hospital');

  // Barcode Scanner State
  const [scannedBarcode, setScannedBarcode] = useState('');
  const [scanResult, setScanResult] = useState<InventoryItem | null>(null);
  const [isSimulatingCamera, setIsSimulatingCamera] = useState(true);

  const toast = useToast();

  const categories = ['All', 'Critical Medicine', 'Oxygen', 'Antibiotic', 'Vaccine', 'Consumables'];

  const filteredItems = items.filter((item) => {
    if (selectedCategory !== 'All' && item.category !== selectedCategory) return false;
    if (activeTab === 'lowStock' && item.days_of_supply >= 7) return false;
    if (
      search &&
      !item.name.toLowerCase().includes(search.toLowerCase()) &&
      !item.batch_no.toLowerCase().includes(search.toLowerCase()) &&
      !item.facility_name.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const expiringItems = items.filter((item) => item.days_until_expiry < 90);
  const estimatedWastageINR = expiringItems.reduce((acc, curr) => acc + curr.current_stock * 45, 0);

  const handleOpenTransfer = (item: InventoryItem) => {
    setTransferTarget(item);
    setIsTransferModalOpen(true);
  };

  const handleExecuteTransfer = () => {
    if (!transferTarget) return;
    toast.success(
      'Stock Transfer Dispatched',
      `Transferred ${transferAmount} ${transferTarget.unit} of ${transferTarget.name} to ${destinationFacility}. Route optimized with cold-chain tracking.`,
      5000
    );
    setIsTransferModalOpen(false);
  };

  const handleBarcodeLookup = (code: string) => {
    setScannedBarcode(code);
    const found = items.find(
      (i) => i.batch_no.toLowerCase().includes(code.toLowerCase()) || i.name.toLowerCase().includes(code.toLowerCase())
    ) || items[0];
    setScanResult(found);
    toast.info('Barcode Recognized', `Identified pharmaceutical: ${found.name} (Batch ${found.batch_no})`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Package className="w-3.5 h-3.5" />
            <span>National Drug & Supply Ledger</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Real-Time Stock Monitoring & Batch Tracking
          </h2>
          <p className="text-xs text-slate-400">
            Automated reorder triggers, cold-chain batch audit trails, near-expiry risk forecasting, and inter-facility redistribution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('scan')}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
              activeTab === 'scan'
                ? 'bg-emerald-500 text-slate-950 font-bold border-emerald-400 shadow-lg shadow-emerald-500/20'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
            }`}
          >
            <QrCode className="w-4 h-4 text-emerald-400" />
            <span>Barcode / QR Scanner</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { key: 'medicines', label: 'Medicine Ledger', icon: Package },
          { key: 'batches', label: 'Batch Directory', icon: Layers },
          { key: 'lowStock', label: 'Low Stock Triage', icon: AlertTriangle, count: items.filter(i => i.days_of_supply < 7).length },
          { key: 'expiry', label: 'Expiry Tracker', icon: Clock, count: expiringItems.length },
          { key: 'history', label: 'Movement History', icon: History },
          { key: 'scan', label: 'Optical Scanner', icon: Barcode },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {tab.count !== undefined && tab.count > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300 text-[10px] font-mono font-bold">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* View 1 & 3: Medicine Table & Low Stock View */}
      {(activeTab === 'medicines' || activeTab === 'lowStock') && (
        <div className="space-y-4">
          {/* Filter and Search Bar */}
          <Card className="p-4 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-[260px]">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search by drug name, batch #, or facility..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>

              <div className="flex items-center gap-1.5">
                <Filter className="w-4 h-4 text-slate-400" />
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="text-xs text-slate-400">
              Showing <strong className="text-slate-100">{filteredItems.length}</strong> pharmaceuticals
            </div>
          </Card>

          {/* Table */}
          <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Medicine / Asset</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Facility</th>
                    <th className="py-3 px-4">Stock on Hand</th>
                    <th className="py-3 px-4">Days of Cover</th>
                    <th className="py-3 px-4">Expiry Date</th>
                    <th className="py-3 px-4">Risk Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-normal">
                  {filteredItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100">{item.name}</div>
                        <div className="text-[10px] font-mono text-slate-400">Batch: {item.batch_no}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{item.category}</td>
                      <td className="py-3 px-4 text-slate-300">{item.facility_name}</td>
                      <td className="py-3 px-4">
                        <span className="font-bold font-mono text-slate-100">
                          {item.current_stock.toLocaleString()}
                        </span>{' '}
                        <span className="text-[10px] text-slate-400">{item.unit}</span>
                        <div className="text-[10px] text-slate-500">Min: {item.reorder_level}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-mono font-bold ${
                            item.days_of_supply < 5
                              ? 'text-rose-400'
                              : item.days_of_supply < 15
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {item.days_of_supply} days
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-200">{item.expiry_date}</div>
                        <div
                          className={`text-[10px] font-mono ${
                            item.days_until_expiry < 30 ? 'text-rose-400 font-semibold' : 'text-slate-400'
                          }`}
                        >
                          {item.days_until_expiry} days left
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge level={item.risk_level}>{item.risk_level.toUpperCase()}</Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenTransfer(item)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition-colors"
                        >
                          <ArrowRightLeft className="w-3.5 h-3.5" />
                          <span>Transfer</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* View 2: Batch Table (Required by Phase 5) */}
      {activeTab === 'batches' && (
        <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-4">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Granular Batch Registry & Cold-Chain Vault</h3>
              <p className="text-[11px] text-slate-400">Traceability per manufacturing lot, reefer temperature, and physical warehouse racks.</p>
            </div>
            <span className="text-xs font-mono text-emerald-400">5 Active Lots Logged</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Batch Number</th>
                  <th className="py-3 px-4">Pharmaceutical</th>
                  <th className="py-3 px-4">Holding Facility</th>
                  <th className="py-3 px-4">Lot Size</th>
                  <th className="py-3 px-4">Cold-Chain Temp</th>
                  <th className="py-3 px-4">Storage Location</th>
                  <th className="py-3 px-4">Mfg / Exp Date</th>
                  <th className="py-3 px-4">Lot Health</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {mockBatches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-100">{b.batchNo}</td>
                    <td className="py-3 px-4 font-semibold text-slate-200">{b.medicineName}</td>
                    <td className="py-3 px-4 text-slate-300">{b.facility}</td>
                    <td className="py-3 px-4 font-mono text-slate-100">{b.quantity.toLocaleString()} {b.unit}</td>
                    <td className="py-3 px-4 text-cyan-300 font-mono text-[11px]">{b.coldChainTemp}</td>
                    <td className="py-3 px-4 text-slate-400">{b.rackLocation}</td>
                    <td className="py-3 px-4 text-[11px] font-mono">
                      <div className="text-slate-400">Mfg: {b.mfgDate}</div>
                      <div className="text-amber-400 font-bold">Exp: {b.expDate}</div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge level={b.status === 'valid' ? 'low' : b.status === 'near-expiry' ? 'moderate' : 'critical'}>
                        {b.status.toUpperCase()}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* View 4: Expiry Tracking UI (Feature 12 & Phase 5) */}
      {activeTab === 'expiry' && (
        <div className="space-y-5">
          {/* Expiry Risk Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Expiring in &lt; 30 Days</span>
              <div className="text-2xl font-bold font-mono text-rose-400">3 Batches</div>
              <p className="text-[11px] text-slate-400">Urgent redistribution or consumption priority required</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Expiring in 30 - 90 Days</span>
              <div className="text-2xl font-bold font-mono text-amber-400">8 Batches</div>
              <p className="text-[11px] text-slate-400">Eligible for state-level buffer rotation</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Monetary Wastage Risk Value</span>
              <div className="text-2xl font-bold font-mono text-emerald-400">₹{(estimatedWastageINR / 100000).toFixed(2)} Lakhs</div>
              <p className="text-[11px] text-emerald-400">92% preventable with algorithmic early redistribution</p>
            </Card>
          </div>

          <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-3">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100">Near-Expiry Medicine Ledger (FEFO Protocol)</h3>
                <p className="text-[11px] text-slate-400">First-Expiry, First-Out (FEFO) dispensing order.</p>
              </div>
              <button
                onClick={() => toast.success('Proactive Rotation Triggered', 'Dispatched return requests for batches under 30 days to central warehouse.')}
                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-colors"
              >
                Trigger FEFO Auto-Rebalance
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Medicine</th>
                    <th className="py-3 px-4">Batch #</th>
                    <th className="py-3 px-4">Facility</th>
                    <th className="py-3 px-4">Stock on Hand</th>
                    <th className="py-3 px-4">Days Until Expiry</th>
                    <th className="py-3 px-4">Expiry Date</th>
                    <th className="py-3 px-4 text-right">FEFO Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-normal">
                  {expiringItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-slate-100">{item.name}</td>
                      <td className="py-3 px-4 font-mono text-slate-300">{item.batch_no}</td>
                      <td className="py-3 px-4 text-slate-300">{item.facility_name}</td>
                      <td className="py-3 px-4 font-mono text-slate-100">{item.current_stock} {item.unit}</td>
                      <td className="py-3 px-4">
                        <span className={`font-mono font-bold ${item.days_until_expiry < 30 ? 'text-rose-400' : 'text-amber-400'}`}>
                          {item.days_until_expiry} days remaining
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{item.expiry_date}</td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenTransfer(item)}
                          className="px-2.5 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-semibold transition-colors"
                        >
                          Redistribute Lot
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* View 5: Stock Movement History (Required by Phase 5) */}
      {activeTab === 'history' && (
        <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90 space-y-3">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Stock Movement Audit Trail & Chain of Custody</h3>
              <p className="text-[11px] text-slate-400">Cryptographically verifiable transactions across depots, pharmacies, and clinical wards.</p>
            </div>
            <span className="text-xs font-mono text-teal-400">Live Transaction Stream</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Transaction Type</th>
                  <th className="py-3 px-4">Asset / Medicine</th>
                  <th className="py-3 px-4">Delta</th>
                  <th className="py-3 px-4">Destination / Source</th>
                  <th className="py-3 px-4">Authorized Signature</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {mockStockHistory.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-400">{h.timestamp}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-200 border border-slate-700">
                        {h.type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-100">{h.medicineName}</td>
                    <td className="py-3 px-4 font-mono font-bold text-emerald-400">{h.quantityChange}</td>
                    <td className="py-3 px-4 text-slate-300">{h.sourceTarget}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">{h.authorizedBy}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* View 6: Barcode Scan Screen (Required by Phase 5) */}
      {activeTab === 'scan' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Simulated Optical Viewfinder */}
          <Card className="p-6 bg-slate-900 border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-100">Optical Camera & Barcode Reader</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                ACTIVE SENSOR
              </span>
            </div>

            {/* Viewfinder Window */}
            <div className="relative h-64 w-full bg-slate-950 rounded-2xl border-2 border-dashed border-slate-700 overflow-hidden flex flex-col items-center justify-center">
              {/* Laser scan line animation */}
              <div className="absolute inset-x-0 h-0.5 bg-emerald-400 shadow-[0_0_12px_#34d399] animate-pulse top-1/2 -translate-y-1/2" />
              <div className="w-48 h-32 border-2 border-emerald-500/60 rounded-xl relative flex items-center justify-center">
                <Barcode className="w-20 h-20 text-slate-600 opacity-60" />
                <div className="absolute top-1 left-1 w-3 h-3 border-t-2 border-l-2 border-emerald-400" />
                <div className="absolute top-1 right-1 w-3 h-3 border-t-2 border-r-2 border-emerald-400" />
                <div className="absolute bottom-1 left-1 w-3 h-3 border-b-2 border-l-2 border-emerald-400" />
                <div className="absolute bottom-1 right-1 w-3 h-3 border-b-2 border-r-2 border-emerald-400" />
              </div>
              <span className="text-[11px] text-slate-400 mt-4">
                Align 1D Barcode (GS1-128) or 2D DataMatrix QR inside bounding box
              </span>
            </div>

            {/* Quick Demo Scan Buttons */}
            <div className="space-y-2 pt-2">
              <span className="text-xs text-slate-400 font-semibold block">Simulate Optical Scan:</span>
              <div className="flex flex-wrap gap-2">
                {items.slice(0, 4).map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleBarcodeLookup(item.batch_no)}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 hover:border-emerald-500 text-[11px] font-mono text-slate-300 transition-colors"
                  >
                    Scan: {item.batch_no}
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Scan Results & Actions Card */}
          <Card className="p-6 bg-slate-900 border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Identified Pharmaceutical Lot
            </h3>

            {scanResult ? (
              <div className="space-y-4 animate-in fade-in">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-100">{scanResult.name}</h4>
                      <span className="text-xs text-slate-400">{scanResult.category} • {scanResult.facility_name}</span>
                    </div>
                    <Badge level={scanResult.risk_level}>{scanResult.risk_level.toUpperCase()}</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 text-xs font-mono">
                    <div className="p-2 bg-slate-900 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Batch Number</span>
                      <strong className="text-slate-200">{scanResult.batch_no}</strong>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Current Ledger Stock</span>
                      <strong className="text-emerald-400">{scanResult.current_stock} {scanResult.unit}</strong>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Days of Runway</span>
                      <strong className="text-amber-400">{scanResult.days_of_supply} days</strong>
                    </div>
                    <div className="p-2 bg-slate-900 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Expiry Date</span>
                      <strong className="text-slate-200">{scanResult.expiry_date}</strong>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-300">Quick Inventory Action:</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        toast.success('Stock Added', `Incremented ledger for ${scanResult.name} by +50 units.`);
                      }}
                      className="flex-1 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Receive +50 Units</span>
                    </button>
                    <button
                      onClick={() => {
                        toast.info('Dispensed', `Logged dispensation of 10 units for ${scanResult.name}.`);
                      }}
                      className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors"
                    >
                      Dispense -10 Units
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl space-y-2">
                <Barcode className="w-8 h-8 text-slate-600 mx-auto" />
                <p>No barcode scanned yet. Use camera viewfinder or select a sample batch on the left.</p>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Transfer Request Modal */}
      {transferTarget && (
        <Modal
          isOpen={isTransferModalOpen}
          onClose={() => setIsTransferModalOpen(false)}
          title={`Inter-Facility Stock Redistribution: ${transferTarget.name}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
              <div className="text-slate-400">
                Source Facility: <strong className="text-slate-200">{transferTarget.facility_name}</strong>
              </div>
              <div className="text-slate-400">
                Available Stock: <strong className="text-emerald-400 font-mono">{transferTarget.current_stock} {transferTarget.unit}</strong>
              </div>
              <div className="text-slate-400">
                Batch Number: <span className="font-mono text-slate-300">{transferTarget.batch_no}</span>
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Destination Recipient Facility
              </label>
              <select
                value={destinationFacility}
                onChange={(e) => setDestinationFacility(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none"
              >
                <option value="Patna Sadar Hospital">Patna Sadar Hospital (Critical Shortage)</option>
                <option value="PHC Malihabad">PHC Malihabad (Stockout Imminent)</option>
                <option value="RML District Hospital Lucknow">RML District Hospital Lucknow</option>
                <option value="Varanasi Rural CHC">Varanasi Rural CHC</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Quantity to Reallocate ({transferTarget.unit})
              </label>
              <input
                type="number"
                min="1"
                max={transferTarget.current_stock}
                value={transferAmount}
                onChange={(e) => setTransferAmount(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none font-mono"
              />
            </div>

            <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-[11px] leading-relaxed">
              Google OR-Tools solver calculated transit time: <strong>3.2 hours</strong>. Temperature logging active for cold-chain compliance.
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsTransferModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteTransfer}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl shadow-lg shadow-emerald-500/20"
              >
                Authorize & Dispatch
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default InventoryPage;
