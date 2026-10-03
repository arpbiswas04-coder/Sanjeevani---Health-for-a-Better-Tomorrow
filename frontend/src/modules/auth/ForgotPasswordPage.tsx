import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { authService } from '@/services/authService';

export const ForgotPasswordPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await authService.requestPasswordReset(username.trim()); setSubmitted(true); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Recovery unavailable.'); }
    finally { setBusy(false); }
  };
  return <div className="min-h-screen bg-slate-950 grid place-items-center p-6">
    <Card className="max-w-md w-full space-y-4 text-slate-200">
      <h1 className="text-xl font-bold">Account Recovery</h1>
      {submitted ? <p>If the account is eligible and delivery is configured, recovery instructions will be delivered. Otherwise contact your administrator.</p>
        : <form onSubmit={submit} className="space-y-4">
          <label htmlFor="recovery-username">Username</label>
          <input id="recovery-username" autoComplete="username" required value={username} onChange={event => setUsername(event.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3" />
          <button disabled={busy} className="bg-emerald-500 text-slate-950 rounded-xl p-3">{busy ? 'Requesting...' : 'Request recovery'}</button>
        </form>}
      {error && <p role="alert">{error}</p>}
      <Link className="text-emerald-400 block" to="/login">Return to sign in</Link>
    </Card>
  </div>;
};
export default ForgotPasswordPage;
