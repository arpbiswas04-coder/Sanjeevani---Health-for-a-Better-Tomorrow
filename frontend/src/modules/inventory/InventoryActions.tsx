import { MutationForm, Options } from '@/components/common/MutationForm';
import { InventoryWithBatch, MedicineView } from '@/services/backendTypes';

export function InventoryActions({facility, medicines, stock}: {facility:string;medicines:MedicineView[];stock:InventoryWithBatch[]}) {
 if(!facility)return null;
 const options:Options={medicine_id:medicines.map(m=>({value:m.id,label:`${m.name} (${m.unit})`})),batch_id:stock.map(s=>({value:s.batch_id,label:`${s.batch.batch_number} (${s.quantity} on hand)`}))};
 return <div className="flex flex-wrap gap-2">
 <MutationForm title="Receive stock" path="/inventory/receive" schema="Receive" permission="inventory.write" fixed={{facility_id:facility}} options={options} validate={b=>b.expires_on<=new Date().toISOString().slice(0,10)?'Stock must expire after today (UTC).':undefined}/>
 <MutationForm title="Issue stock" path="/inventory/issue" schema="Issue" permission="inventory.write" fixed={{facility_id:facility}} options={options} confirm="Issue this quantity from the selected facility. The backend chooses usable batches by FEFO and records the stock deduction."/>
 <MutationForm title="Adjust stock" path="/inventory/adjust" schema="Adjustment" permission="inventory.write" fixed={{facility_id:facility}} options={options} confirm="Apply this signed stock change and record its reference in the transaction ledger." validate={b=>b.quantity===0||(['DAMAGE','EXPIRED','RECALL'].includes(b.kind)&&b.quantity>0)||(b.kind==='RETURN'&&b.quantity<0)?'Use a nonzero quantity with the correct sign for this adjustment kind.':undefined}/>
 </div>;
}
