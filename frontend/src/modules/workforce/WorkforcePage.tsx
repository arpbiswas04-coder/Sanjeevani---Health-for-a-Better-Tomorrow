import React, { useState } from 'react';
import { MOCK_WORKFORCE } from '@/services/mockData';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/hooks/useToast';
import {
  Users,
  UserCheck,
  Stethoscope,
  AlertTriangle,
  ShieldCheck,
  Clock,
  Search,
  Calendar,
  CheckCircle2,
  XCircle,
  PhoneCall,
  UserPlus,
  Filter,
} from 'lucide-react';

interface StaffMember {
  id: string;
  name: string;
  role: string;
  department: string;
  facility: string;
  phone: string;
  status: 'On Duty' | 'On Call' | 'Off Duty' | 'On Leave';
  checkInTime?: string;
  assignedPatients: number;
}

const mockStaffDirectory: StaffMember[] = [
  { id: 'STF-101', name: 'Dr. Vikramaditya Sen', role: 'Chief Intensivist (HOD)', department: 'Emergency & Trauma ICU', facility: 'RML Hospital Lucknow', phone: '+91 98390 11201', status: 'On Duty', checkInTime: '07:45 AM', assignedPatients: 6 },
  { id: 'STF-102', name: 'Dr. Ananya Sharma', role: 'Senior Pediatrician', department: 'Pediatric & Neonatal Care', facility: 'Patna Sadar Hospital', phone: '+91 94310 88204', status: 'On Duty', checkInTime: '08:00 AM', assignedPatients: 14 },
  { id: 'STF-103', name: 'Dr. Tariq Siddiqui', role: 'General Physician', department: 'General Medicine & OPD', facility: 'PHC Malihabad', phone: '+91 98892 44319', status: 'On Duty', checkInTime: '08:15 AM', assignedPatients: 38 },
  { id: 'STF-104', name: 'Nurse Supv. Sunita Roy', role: 'Head Nursing Officer', department: 'Emergency & Trauma ICU', facility: 'RML Hospital Lucknow', phone: '+91 97210 55102', status: 'On Duty', checkInTime: '06:55 AM', assignedPatients: 12 },
  { id: 'STF-105', name: 'Dr. Meenakshi Iyer', role: 'Consultant Pulmonologist', department: 'General Medicine & OPD', facility: 'Varanasi Rural CHC', phone: '+91 99180 33201', status: 'On Call', assignedPatients: 0 },
  { id: 'STF-106', name: 'Paramedic Alok Dubey', role: 'Emergency Medical Technician', department: 'Emergency & Trauma ICU', facility: 'AIIMS New Delhi', phone: '+91 98110 77209', status: 'On Duty', checkInTime: '07:30 AM', assignedPatients: 4 },
];

export const WorkforcePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ratios' | 'personnel' | 'attendance'>('ratios');
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('All');
  const toast = useToast();

  const filteredStaff = mockStaffDirectory.filter((s) => {
    if (deptFilter !== 'All' && s.department !== deptFilter) return false;
    if (
      search &&
      !s.name.toLowerCase().includes(search.toLowerCase()) &&
      !s.role.toLowerCase().includes(search.toLowerCase()) &&
      !s.facility.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const handlePageStaff = (staff: StaffMember) => {
    toast.info('Emergency Page Sent', `Transmitted high-priority audio page to ${staff.name} (${staff.phone}).`);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-pink-500/10 text-pink-400 border border-pink-500/30">
            <Users className="w-3.5 h-3.5" />
            <span>Clinical & Paramedical Roster</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Workforce Telemetry, Personnel Management & Attendance
          </h2>
          <p className="text-xs text-slate-400">
            Departmental doctor-to-patient ratios, live biometric attendance logging, and emergency rota paging.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 p-1 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab('ratios')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'ratios'
                ? 'bg-pink-500 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Ratios & Load
          </button>
          <button
            onClick={() => setActiveTab('personnel')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'personnel'
                ? 'bg-pink-500 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Personnel Directory
          </button>
          <button
            onClick={() => setActiveTab('attendance')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'attendance'
                ? 'bg-pink-500 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Biometric Attendance
          </button>
        </div>
      </div>

      {/* Tab 1: Doctor-to-Patient Ratios & Department Telemetry (Feature 38) */}
      {activeTab === 'ratios' && (
        <div className="space-y-6">
          {/* WHO Benchmark Banner */}
          <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5">
              <Stethoscope className="w-5 h-5 text-purple-400 shrink-0" />
              <div>
                <span className="font-bold text-purple-200">WHO Guideline Benchmark: 1 Doctor per 1,000 Population</span>
                <p className="text-slate-400 text-[11px]">
                  Emergency ICU Target: 1:4 • General Medicine Target: 1:20 • Current National Network Average: 1:24
                </p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 font-mono font-bold text-[11px] self-start sm:self-center">
              Network Stress: MODERATE
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {MOCK_WORKFORCE.map((w) => (
              <Card key={w.department} className="space-y-4">
                <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="font-bold text-sm text-slate-100">{w.department}</h3>
                    <span className="text-xs text-slate-400">Active Shift Telemetry</span>
                  </div>
                  <Badge level={w.stress_index}>{w.stress_index.toUpperCase()} LOAD</Badge>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                  <div className="p-2.5 bg-slate-950/70 rounded-xl">
                    <span className="text-[10px] text-slate-500 block">Doctors On Duty</span>
                    <strong className="text-emerald-400 text-sm">{w.doctors_on_duty}</strong>
                  </div>
                  <div className="p-2.5 bg-slate-950/70 rounded-xl">
                    <span className="text-[10px] text-slate-500 block">Nurses & Paramedics</span>
                    <strong className="text-teal-400 text-sm">{w.nurses_on_duty}</strong>
                  </div>
                  <div className="p-2.5 bg-slate-950/70 rounded-xl">
                    <span className="text-[10px] text-slate-500 block">Doctor : Patient</span>
                    <strong className="text-purple-400 text-sm">{w.doctor_patient_ratio}</strong>
                  </div>
                </div>

                <div className="space-y-1.5 pt-1">
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Shift Attendance:</span>
                    <strong className="text-slate-200 font-mono">{w.shift_attendance_pct}%</strong>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${w.shift_attendance_pct}%` }}
                    />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Personnel Management UI (Feature 33) */}
      {activeTab === 'personnel' && (
        <div className="space-y-4">
          <Card className="p-4 bg-slate-900/90 border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-[240px]">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search doctor, nurse, license, or facility..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-pink-500"
                />
              </div>

              <div className="flex items-center gap-1.5">
                <Filter className="w-4 h-4 text-slate-400" />
                <select
                  value={deptFilter}
                  onChange={(e) => setDeptFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-xs text-slate-200 rounded-xl px-2.5 py-1.5 focus:outline-none"
                >
                  <option value="All">All Departments</option>
                  <option value="Emergency & Trauma ICU">Emergency ICU</option>
                  <option value="Pediatric & Neonatal Care">Pediatric Care</option>
                  <option value="General Medicine & OPD">General Medicine</option>
                </select>
              </div>
            </div>

            <button
              onClick={() => toast.success('Staff Requisition Opened', 'Transmitted request to District CMO reserve roster.')}
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-pink-500 hover:bg-pink-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-colors"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Request Medical Staff</span>
            </button>
          </Card>

          <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Staff Member</th>
                    <th className="py-3 px-4">Clinical Role</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Facility</th>
                    <th className="py-3 px-4">Active Status</th>
                    <th className="py-3 px-4">Patient Load</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-normal">
                  {filteredStaff.map((staff) => (
                    <tr key={staff.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-100">{staff.name}</div>
                        <div className="text-[10px] font-mono text-slate-400">{staff.id} • {staff.phone}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{staff.role}</td>
                      <td className="py-3 px-4 text-pink-300">{staff.department}</td>
                      <td className="py-3 px-4 text-slate-300">{staff.facility}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            staff.status === 'On Duty'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : staff.status === 'On Call'
                              ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              staff.status === 'On Duty' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                            }`}
                          />
                          {staff.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <strong className="text-slate-100">{staff.assignedPatients}</strong> patients
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handlePageStaff(staff)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-colors"
                        >
                          <PhoneCall className="w-3 h-3 text-pink-400" />
                          <span>Page</span>
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

      {/* Tab 3: Attendance UI (Feature 34) */}
      {activeTab === 'attendance' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Total Shift Headcount</span>
              <div className="text-2xl font-bold font-mono text-slate-100">142</div>
              <p className="text-[11px] text-slate-400">Morning Shift (07:00 - 15:00)</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Biometric Check-ins</span>
              <div className="text-2xl font-bold font-mono text-emerald-400">134 (94.4%)</div>
              <p className="text-[11px] text-emerald-400">Facial & RFID terminal verified</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">On Standby / Call</span>
              <div className="text-2xl font-bold font-mono text-cyan-400">6 Officers</div>
              <p className="text-[11px] text-cyan-400">Radius &lt; 15 mins to emergency room</p>
            </Card>

            <Card className="p-4 bg-slate-900 border-slate-800 space-y-1">
              <span className="text-xs text-slate-400">Authorized Medical Leave</span>
              <div className="text-2xl font-bold font-mono text-slate-400">2 Personnel</div>
              <p className="text-[11px] text-slate-500">Substituted by reserve rota</p>
            </Card>
          </div>

          <Card className="p-0 overflow-hidden border-slate-800 bg-slate-900/90">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100">Live Biometric Attendance Stream</h3>
                <p className="text-[11px] text-slate-400">Aadhaar-enabled Biometric Attendance System (AeBAS) telemetry feed.</p>
              </div>
              <span className="text-xs font-mono text-emerald-400">Sync: 100% Online</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Staff Member</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Check-in Timestamp</th>
                    <th className="py-3 px-4">Terminal Device</th>
                    <th className="py-3 px-4">Verification</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-normal">
                  {mockStaffDirectory.map((staff) => (
                    <tr key={staff.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-100">{staff.name}</div>
                        <div className="text-[10px] text-slate-400">{staff.role}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{staff.department}</td>
                      <td className="py-3 px-4 font-mono text-emerald-400">{staff.checkInTime || 'N/A (On Call)'}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">BIO-GATEWAY-LKO-02</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          RFID + Iris Verified
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <Badge level={staff.status === 'On Duty' ? 'low' : 'info'}>
                          {staff.status.toUpperCase()}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default WorkforcePage;
