import React from 'react';
import { Card } from '@/components/ui/Card';
import { PageHeading, Unavailable } from '@/components/common/BackendData';
import { ReportsPanel } from '@/modules/analytics/ReportsPanel';
export const EmergencyPage: React.FC = () => <div className="space-y-6"><div className="rounded-2xl p-6 border border-rose-500/30 bg-gradient-to-r from-rose-950/60 via-slate-900 to-slate-900"><PageHeading title="Emergency Command & Crisis Mobilization" description="Recorded emergency reports are available below. No crisis activation state is inferred."/></div><div className="grid grid-cols-1 md:grid-cols-2 gap-5"><Card><h3 className="font-bold text-sm mb-4">Vulnerability Deficit Priority Matrix</h3><Unavailable>Vulnerability scores, crisis polygons and fleet mobilization have no configured backend endpoint.</Unavailable></Card><Card><h3 className="font-bold text-sm mb-4">Scenario Simulation Engine</h3><Unavailable>What-if simulations and emergency override controls are not connected. No simulation or dispatch is reported as successful.</Unavailable></Card></div><ReportsPanel/></div>;
export default EmergencyPage;
