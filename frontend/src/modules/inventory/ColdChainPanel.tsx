import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { DataPanel, controlClass } from '@/components/common/BackendData';
export function ColdChainPanel({ facility }: { facility: string }) {
  const [start, setStart] = useState(''); const [end, setEnd] = useState('');
  const columns = [{key:'observed_at',label:'Observed at'},{key:'temperature',label:'Temperature °C'},{key:'minimum',label:'Minimum °C'},{key:'maximum',label:'Maximum °C'},{key:'excursion',label:'Excursion'}];
  return <div className="space-y-4"><DataPanel key={facility} title="Cold-chain observations" path="/operations/temperatures" params={{facility_id:facility}} permission="inventory.read" enabled={!!facility} columns={[...columns,{key:'shipment_id',label:'Shipment ID'},{key:'source',label:'Source'}]} />
    <Card className="flex flex-wrap gap-3"><label className="text-xs">Series start (UTC)<input aria-label="Cold-chain start" className={controlClass} type="datetime-local" value={start} onChange={e => setStart(e.target.value)} /></label><label className="text-xs">Series end (UTC)<input aria-label="Cold-chain end" className={controlClass} type="datetime-local" value={end} onChange={e => setEnd(e.target.value)} /></label></Card>
    <DataPanel key={`${facility}-${start}-${end}`} title="Cold-chain time series" path="/cold-chain/series" params={{facility_id:facility,start:start ? `${start}:00Z` : undefined,end:end ? `${end}:00Z` : undefined}} permission="inventory.read" enabled={!!facility && !!start && !!end} columns={columns} />
  </div>;
}
