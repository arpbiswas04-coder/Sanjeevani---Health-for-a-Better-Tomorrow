import React from 'react';
import { Card } from '@/components/ui/Card';
import { useAuthStore } from '@/store/authStore';
import { ROLE_LABELS } from '@/types/auth';

export const ProfilePage: React.FC = () => {
  const { user } = useAuthStore();
  if (!user) return null;
  return <div className="max-w-4xl mx-auto space-y-6">
    <h2 className="text-2xl font-bold text-slate-100">User Profile & Credentials</h2>
    <Card className="space-y-4 text-slate-200">
      <h3 className="font-bold">{user.name}</h3>
      <p>{ROLE_LABELS[user.role]}</p>
      <dl className="space-y-2 text-sm">
        <dt>User ID</dt><dd>{user.id}</dd>
        <dt>Backend roles</dt><dd>{user.backendRoles?.join(', ') || 'None assigned'}</dd>
        <dt>Scope</dt><dd>{user.scopeMode}</dd>
        <dt>Assigned facilities</dt><dd>{user.facilityIds?.join(', ') || 'None assigned'}</dd>
        <dt>Assigned districts</dt><dd>{user.districtIds?.join(', ') || 'None assigned'}</dd>
        <dt>Permissions</dt><dd>{user.backendPermissions?.join(', ') || 'None assigned'}</dd>
      </dl>
    </Card>
  </div>;
};
export default ProfilePage;
