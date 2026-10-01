import React, { useState } from 'react';
import {
  ShieldCheck,
  Users,
  Server,
  Key,
  Database,
  Lock,
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  FileText,
  Search,
  Sliders,
  Radio,
  Cpu,
} from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { useUIStore } from '@/store/uiStore';

interface SystemUser {
  id: string;
  name: string;
  email: string;
  role: 'National Admin' | 'State Officer' | 'Medical Superintendent' | 'Pharmacist' | 'Logistics Lead' | 'Field Worker';
  facility: string;
  mfaEnrolled: boolean;
  status: 'Active' | 'Suspended' | 'Pending Verification';
  lastLogin: string;
}

interface EdgeNode {
  id: string;
  facility: string;
  ipAddress: string;
  privacyBudgetEpsilon: number;
  status: 'Online (Syncing)' | 'Training' | 'Degraded' | 'Offline';
  roundSynced: number;
}

interface AuditLog {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity: string;
  ip: string;
  status: 'SUCCESS' | 'ALERT' | 'DENIED';
}

const initialUsers: SystemUser[] = [
  {
    id: 'USR-001',
    name: 'Dr. Aarav Patel',
    email: 'aarav.patel@mohfw.gov.in',
    role: 'National Admin',
    facility: 'Ministry of Health Command HQ, New Delhi',
    mfaEnrolled: true,
    status: 'Active',
    lastLogin: '10 mins ago',
  },
  {
    id: 'USR-002',
    name: 'Dr. Sunita Rao',
    email: 's.rao@health.karnataka.gov.in',
    role: 'State Officer',
    facility: 'Karnataka Directorate of Health Services',
    mfaEnrolled: true,
    status: 'Active',
    lastLogin: '1 hour ago',
  },
  {
    id: 'USR-003',
    name: 'Dr. Rajesh K. Sharma',
    email: 'ms@aiimsdelhi.edu.in',
    role: 'Medical Superintendent',
    facility: 'AIIMS New Delhi Trauma Center',
    mfaEnrolled: true,
    status: 'Active',
    lastLogin: '25 mins ago',
  },
  {
    id: 'USR-004',
    name: 'Pooja Verma, RPh',
    email: 'p.verma@patnahospital.org',
    role: 'Pharmacist',
    facility: 'Patna District Civil Hospital',
    mfaEnrolled: true,
    status: 'Active',
    lastLogin: '3 hours ago',
  },
  {
    id: 'USR-005',
    name: 'Vikram Sengupta',
    email: 'v.sengupta@wbhealth.gov.in',
    role: 'Logistics Lead',
    facility: 'Eastern Regional Medical Supply Depot, Kolkata',
    mfaEnrolled: false,
    status: 'Pending Verification',
    lastLogin: 'Never',
  },
];

const initialNodes: EdgeNode[] = [
  {
    id: 'EDGE-DL-01',
    facility: 'AIIMS New Delhi Edge Cluster',
    ipAddress: '10.14.88.21',
    privacyBudgetEpsilon: 0.85,
    status: 'Online (Syncing)',
    roundSynced: 42,
  },
  {
    id: 'EDGE-MH-02',
    facility: 'KEM Hospital Mumbai Edge',
    ipAddress: '10.22.41.9',
    privacyBudgetEpsilon: 0.90,
    status: 'Training',
    roundSynced: 42,
  },
  {
    id: 'EDGE-KA-03',
    facility: 'Victoria Hospital Bengaluru Edge',
    ipAddress: '10.33.12.104',
    privacyBudgetEpsilon: 0.88,
    status: 'Online (Syncing)',
    roundSynced: 42,
  },
  {
    id: 'EDGE-BR-04',
    facility: 'Patna Civil Hospital Edge Rig',
    ipAddress: '10.66.7.15',
    privacyBudgetEpsilon: 0.92,
    status: 'Degraded',
    roundSynced: 41,
  },
];

const initialLogs: AuditLog[] = [
  {
    id: 'LOG-9921',
    timestamp: '2026-09-29 22:45:12',
    actor: 'Dr. Aarav Patel (National Admin)',
    action: 'EMERGENCY_OVERRIDE_TRIGGER',
    entity: 'DEFCON-1 Bihar Regional Stock Routing',
    ip: '103.21.144.9',
    status: 'ALERT',
  },
  {
    id: 'LOG-9920',
    timestamp: '2026-09-29 22:30:05',
    actor: 'Dr. Sunita Rao (State Officer)',
    action: 'RESOURCE_ALLOCATION_UPDATE',
    entity: 'Mysuru Bed Quota Rebalancing (+25 ICU)',
    ip: '103.25.10.14',
    status: 'SUCCESS',
  },
  {
    id: 'LOG-9919',
    timestamp: '2026-09-29 22:15:40',
    actor: 'Automated FedML Node (EDGE-DL-01)',
    action: 'GRADIENT_UPLOAD_SYNC',
    entity: 'Round #42 Tensor Parameters (dp_epsilon=0.85)',
    ip: '10.14.88.21',
    status: 'SUCCESS',
  },
  {
    id: 'LOG-9918',
    timestamp: '2026-09-29 21:55:00',
    actor: 'Unknown IP (Port Scan)',
    action: 'UNAUTHORIZED_API_ACCESS',
    entity: '/api/v1/auth/internal-keys',
    ip: '198.51.100.44',
    status: 'DENIED',
  },
];

export const AdminPage: React.FC = () => {
  const [users, setUsers] = useState<SystemUser[]>(initialUsers);
  const [nodes, setNodes] = useState<EdgeNode[]>(initialNodes);
  const [logs] = useState<AuditLog[]>(initialLogs);
  const [activeTab, setActiveTab] = useState<'users' | 'nodes' | 'logs' | 'system'>('users');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);

  // New user form state
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<SystemUser['role']>('Medical Superintendent');
  const [newFacility, setNewFacility] = useState('');

  const toast = useToast();
  const { activeRole, setActiveRole } = useUIStore();

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newEmail) return;

    const user: SystemUser = {
      id: `USR-00${users.length + 1}`,
      name: newName,
      email: newEmail,
      role: newRole,
      facility: newFacility || 'General Medical Complex',
      mfaEnrolled: false,
      status: 'Active',
      lastLogin: 'Never',
    };

    setUsers([...users, user]);
    setIsAddUserOpen(false);
    setNewName('');
    setNewEmail('');
    setNewFacility('');

    toast.success(
      'User Account Created',
      `${user.name} provisioned with role [${user.role}]. Activation invite sent.`
    );
  };

  const handleRotateKey = (nodeId: string) => {
    toast.info(
      'Cryptographic Key Rotated',
      `Zero-Knowledge TLS token for ${nodeId} renewed with 4096-bit RSA entropy.`
    );
  };

  const handleToggleUserStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) => {
        if (u.id === id) {
          const nextStatus = u.status === 'Active' ? 'Suspended' : 'Active';
          return { ...u, status: nextStatus };
        }
        return u;
      })
    );
    toast.info(
      'User Status Updated',
      `User account ${id} state changed in directory.`
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
                Administration & System Governance
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Feature #104
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400">
                RBAC access control, federated edge key pairing, audit compliance, and infrastructure telemetry.
              </p>
            </div>
          </div>
        </div>

        {/* Global Role Simulator & Action */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <span className="text-xs text-slate-400 font-bold">Simulate:</span>
            <select
              value={activeRole}
              onChange={(e) => setActiveRole(e.target.value as any)}
              className="bg-slate-800 text-xs font-bold text-emerald-400 border border-slate-700 rounded-lg px-2 py-1 focus:outline-none"
            >
              <option value="national_officer">National Command Officer</option>
              <option value="state_officer">State Surveillance Officer</option>
              <option value="district_officer">District Health Officer</option>
              <option value="facility_admin">Hospital Superintendent</option>
              <option value="logistics_coordinator">Logistics Coordinator</option>
              <option value="doctor">Treating Physician</option>
            </select>
          </div>

          {activeTab === 'users' && (
            <button
              onClick={() => setIsAddUserOpen(true)}
              className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-colors shadow-sm shadow-purple-600/30"
            >
              <Plus className="w-4 h-4" />
              Add User
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex p-1 bg-slate-900 border border-slate-800 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'users'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          User RBAC Directory ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('nodes')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'nodes'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Server className="w-4 h-4" />
          Edge Node Pairing ({nodes.length})
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'logs'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          Audit Trails ({logs.length})
        </button>
        <button
          onClick={() => setActiveTab('system')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
            activeTab === 'system'
              ? 'bg-purple-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-4 h-4" />
          System Telemetry
        </button>
      </div>

      {/* Tab 1: RBAC User Directory */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4 p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
            <div className="flex items-center gap-2 flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search staff by name, email, or facility..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent text-xs text-slate-200 placeholder-slate-500 w-full focus:outline-none"
              />
            </div>
            <div className="text-xs text-slate-400">
              Active directory: <span className="font-bold text-slate-200">{users.length}</span> security principals
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-mono">
                <tr>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Assigned Facility / Jurisdiction</th>
                  <th className="py-3 px-4">MFA State</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Last Activity</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {users
                  .filter(
                    (u) =>
                      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      u.facility.toLowerCase().includes(searchQuery.toLowerCase())
                  )
                  .map((user) => (
                    <tr key={user.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-100">{user.name}</div>
                        <div className="text-[11px] text-slate-400">{user.email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-purple-300 border border-purple-500/20">
                          {user.role}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300 max-w-xs truncate">{user.facility}</td>
                      <td className="py-3.5 px-4">
                        {user.mfaEnrolled ? (
                          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Enrolled (TOTP)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-bold">
                            <AlertCircle className="w-3.5 h-3.5" /> Required
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            user.status === 'Active'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : user.status === 'Suspended'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {user.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">{user.lastLogin}</td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleToggleUserStatus(user.id)}
                          className="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300"
                        >
                          {user.status === 'Active' ? 'Suspend' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Edge Node Pairing */}
      {activeTab === 'nodes' && (
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Key className="w-6 h-6 text-purple-400" />
              <div>
                <h3 className="text-sm font-bold text-slate-100">Federated Edge Compute Node Keyrings</h3>
                <p className="text-xs text-slate-400">
                  Manage zero-trust TLS credentials and Differential Privacy epsilon allocations for hospital compute clusters.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                toast.success(
                  'Node Enrolment Token Generated',
                  'One-time registration secret: SANJEEVANI-NODE-7819-KEY valid for 30 mins.'
                );
              }}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-colors"
            >
              Generate Enrolment Token
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {nodes.map((node) => (
              <div key={node.id} className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-xs font-bold text-purple-400">{node.id}</span>
                    <h4 className="text-sm font-bold text-slate-100">{node.facility}</h4>
                    <span className="font-mono text-[11px] text-slate-500">{node.ipAddress}</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      node.status.includes('Online')
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : node.status === 'Training'
                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {node.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-500">Differential Privacy ε:</span>
                    <div className="font-mono font-bold text-slate-200">{node.privacyBudgetEpsilon} (High Anonymity)</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500">Synced Round:</span>
                    <div className="font-mono font-bold text-slate-200">Round #{node.roundSynced}</div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    onClick={() => handleRotateKey(node.id)}
                    className="flex items-center gap-1 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" /> Rotate TLS Keys
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Audit Trails */}
      {activeTab === 'logs' && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase font-mono">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Timestamp (UTC+05:30)</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Resource Target</th>
                <th className="py-3 px-4">Origin IP</th>
                <th className="py-3 px-4">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-300">{log.id}</td>
                  <td className="py-3 px-4 text-slate-400">{log.timestamp}</td>
                  <td className="py-3 px-4 font-sans text-slate-200">{log.actor}</td>
                  <td className="py-3 px-4 font-bold text-purple-300">{log.action}</td>
                  <td className="py-3 px-4 font-sans text-slate-300">{log.entity}</td>
                  <td className="py-3 px-4 text-slate-400">{log.ip}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        log.status === 'SUCCESS'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : log.status === 'ALERT'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 4: System Health & Pool Telemetry */}
      {activeTab === 'system' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400">
              <Database className="w-5 h-5" />
              <h4 className="font-bold text-sm text-slate-100">PostgreSQL Connection Pool</h4>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Active Connections:</span>
                <span className="font-mono font-bold text-slate-100">18 / 100</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Pool Wait Queue:</span>
                <span className="font-mono font-bold text-slate-100">0 ms</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Replication Lag:</span>
                <span className="font-mono font-bold text-emerald-400">1.2 ms (Synchronous)</span>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-cyan-400">
              <Radio className="w-5 h-5" />
              <h4 className="font-bold text-sm text-slate-100">Redis Cache & Pub/Sub Mesh</h4>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Memory Allocated:</span>
                <span className="font-mono font-bold text-slate-100">412 MB / 2 GB</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Cache Hit Ratio:</span>
                <span className="font-mono font-bold text-emerald-400">96.8%</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Active Channels:</span>
                <span className="font-mono font-bold text-slate-100">14 telemetry topics</span>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-purple-400">
              <Server className="w-5 h-5" />
              <h4 className="font-bold text-sm text-slate-100">FedML Parameter Server</h4>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-400">
                <span>Aggregation Engine:</span>
                <span className="font-mono font-bold text-slate-100">FedProx + FedAvg</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Weight Verification:</span>
                <span className="font-mono font-bold text-emerald-400">SHA-256 Validated</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Active Nodes:</span>
                <span className="font-mono font-bold text-slate-100">48 Hospitals Synced</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      {isAddUserOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-400" />
                Provision Platform Personnel
              </h3>
              <button
                onClick={() => setIsAddUserOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Kavita Nair"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                  Official Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="kavita.nair@health.gov.in"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                    System Role
                  </label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  >
                    <option value="National Admin">National Admin</option>
                    <option value="State Officer">State Officer</option>
                    <option value="Medical Superintendent">Medical Superintendent</option>
                    <option value="Pharmacist">Pharmacist</option>
                    <option value="Logistics Lead">Logistics Lead</option>
                    <option value="Field Worker">Field Worker</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">
                    Facility Jurisdiction
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. District Hospital"
                    value={newFacility}
                    onChange={(e) => setNewFacility(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddUserOpen(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold shadow-md shadow-purple-600/30"
                >
                  Provision & Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPage;
