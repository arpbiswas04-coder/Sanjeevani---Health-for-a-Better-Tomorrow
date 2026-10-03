import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';

export const MFAPage: React.FC = () => <div className="min-h-screen bg-slate-950 grid place-items-center p-6">
  <Card className="max-w-md space-y-4 text-slate-200">
    <h1 className="text-xl font-bold">Multi-factor authentication</h1>
    <p>Enter your MFA proof with your username and password on the sign-in page. The backend must verify it before issuing a session.</p>
    <p>If your administrator has not configured an MFA provider, contact them for assistance.</p>
    <Link className="text-emerald-400" to="/login">Return to sign in</Link>
  </Card>
</div>;
export default MFAPage;
