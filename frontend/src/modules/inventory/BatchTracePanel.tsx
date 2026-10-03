import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useBackendData } from '@/hooks/useBackendData';
import { DataState, Fields, RecordTable, buttonClass } from '@/components/common/BackendData';
export function BatchTracePanel({ batch }: { batch: string }) {
  const [offset, setOffset] = useState(0);
  const query = useBackendData<{batch:object;inventory:object[];transactions:object[]}>(`/batches/${batch}/trace`, {offset,limit:50}, 'inventory.read');
  const more = query.data && (query.data.inventory.length === 50 || query.data.transactions.length === 50);
  return <Card className="space-y-4"><h3 className="text-sm font-bold">Batch traceability</h3><DataState query={query}>
    {query.data && <><Fields value={query.data.batch} /><h4 className="text-xs font-bold">Stock locations in your scope</h4><RecordTable rows={query.data.inventory} columns={[{key:'facility_id',label:'Facility ID'},{key:'quantity',label:'Quantity'},{key:'reserved',label:'Reserved'}]} /><h4 className="text-xs font-bold">Transaction history in your scope</h4><RecordTable rows={query.data.transactions} columns={[{key:'created_at',label:'Recorded at'},{key:'kind',label:'Kind'},{key:'quantity',label:'Quantity'},{key:'reference',label:'Reference'}]} /></>}
  </DataState><div className="flex items-center gap-3 text-xs"><button className={buttonClass} disabled={!offset || query.isFetching} onClick={() => setOffset(Math.max(0,offset-50))}>Previous trace page</button><span>Page {offset/50+1}; up to 50 rows per section</span><button className={buttonClass} disabled={!more || query.isFetching} onClick={() => setOffset(offset+50)}>Next trace page</button></div></Card>;
}
