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
} from 'lucide-react';

export const InventoryPage: React.FC = () => {
  const [items, setItems] = useState<InventoryItem[]>(MOCK_INVENTORY);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [transferTarget, setTransferTarget] = useState<InventoryItem | null>(null);
  const [transferAmount, setTransferAmount] = useState(50);
  const [destinationFacility, setDestinationFacility] = useState('Patna Sadar Hospital');
  const toast = useToast();

  const categories = ['All', 'Critical Medicine', 'Oxygen', 'Antibiotic', 'Vaccine', 'Consumables'];

  const filteredItems = items.filter((item) => {
    if (selectedCategory !== 'All' && item.category !== selectedCategory) return false;
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
            Automated low-stock threshold triggers, consumption velocities, and batch traceability.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              toast.info('Barcode Scanner Active', 'Point mobile or optical camera at medicine packaging barcode/QR code.');
            }}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <QrCode className="w-4 h-4 text-emerald-400" />
            <span>Scan Barcode</span>
          </button>
        </div>
      </div>

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
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-400">
          Showing <strong className="text-slate-100">{filteredItems.length}</strong> monitored pharmaceuticals
        </div>
      </Card>

      {/* Inventory Data Table */}
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
