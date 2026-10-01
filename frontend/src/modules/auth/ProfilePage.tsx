import React from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useUIStore } from '@/store/uiStore';
import { User, Shield, Building, Key, Mail, Phone, Calendar } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { activeRole } = useUIStore();

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100">User Profile & Credentials</h2>
        <p className="text-xs text-slate-400">Authenticated personnel identity, cryptographic keypair, and role permissions.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex flex-col items-center text-center p-6 space-y-4">
          <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-2xl font-black text-slate-950 shadow-xl shadow-emerald-500/20">
            SG
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-100">Dr. Anand Verma</h3>
            <span className="text-xs text-slate-400">Chief Medical Officer (CMO)</span>
          </div>
          <Badge level="low">{activeRole.toUpperCase()}</Badge>
          <div className="w-full pt-3 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Security Clearance:</span>
              <strong className="text-emerald-400 font-mono">LEVEL-4</strong>
            </div>
            <div className="flex justify-between">
              <span>Hardware Token:</span>
              <strong className="text-cyan-400 font-mono">FIDO2 Active</strong>
            </div>
          </div>
        </Card>

        <Card className="md:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-800 pb-2">
            Official Organization Attributes
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">Assigned Node</span>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Building className="w-4 h-4 text-emerald-400" />
                <span>AIIMS New Delhi Cluster</span>
              </div>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">Official Email</span>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Mail className="w-4 h-4 text-cyan-400" />
                <span>director.verma@sanjeevani.gov.in</span>
              </div>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">Emergency Hotline</span>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Phone className="w-4 h-4 text-purple-400" />
                <span>+91 11 2659-4820</span>
              </div>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">Cryptographic Key Fingerprint</span>
              <div className="font-mono text-emerald-300 text-[11px] truncate flex items-center gap-1.5">
                <Key className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>e3b0c44298fc1c149afbf4c8996</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ProfilePage;
