import React, { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { useCapability } from '@/hooks/useBackendData';
import { sendData } from '@/services/dataApi';
import { ApiError } from '@/services/httpClient';
import { mutationSchemas } from '@/services/mutationSchemas';
import { Modal } from '@/components/ui/Modal';
import { DataError, Fields, buttonClass, controlClass } from './BackendData';

type Schema = { type?: string; format?: string; title?: string; default?: unknown; enum?: readonly unknown[]; anyOf?: readonly Schema[]; $ref?: string; properties?: Record<string, Schema>; required?: readonly string[]; items?: Schema; minimum?: number; maximum?: number; exclusiveMinimum?: number; minLength?: number; maxLength?: number; minItems?: number; maxItems?: number };
export type Values = Record<string, any>;
export type Options = Record<string, { value: string; label: string }[]>;
const schemas = mutationSchemas as unknown as Record<string, Schema>;
function resolve(schema: Schema): Schema { return schema.$ref ? schemas[schema.$ref.split('/').pop()!] : schema.anyOf ? resolve(schema.anyOf.find(s => s.type !== 'null')!) : schema; }
function initial(schema: Schema, defaults: Values): Values {
  return Object.fromEntries(Object.entries(schema.properties || {}).filter(([k]) => k !== 'idempotency_key').map(([k,s]) => {
    const field = resolve(s);
    return [k, defaults[k] ?? s.default ?? (field.type === 'array' ? [initial(resolve(field.items!), {})] : field.type === 'boolean' ? false : '')];
  }));
}
function payloadFor(schema: Schema, values: Values): Values {
  const result: Values = {};
  for (const [key, original] of Object.entries(schema.properties || {})) {
    if (key === 'idempotency_key') continue;
    const s = resolve(original), value = values[key];
    if (value === '' || value == null) { if (schema.required?.includes(key)) throw new Error(`${key.replace(/_/g,' ')} is required.`); continue; }
    if (s.type === 'array') result[key] = value.map((item: Values) => payloadFor(resolve(s.items!), item));
    else if (s.format === 'date-time') result[key] = new Date(value).toISOString();
    else if (s.type === 'number' || s.type === 'integer') {
      const n = Number(value); if (!Number.isFinite(n) || (s.type === 'integer' && !Number.isInteger(n))) throw new Error(`${key} must be a valid ${s.type}.`);
      if ((s.minimum !== undefined && n < s.minimum) || (s.maximum !== undefined && n > s.maximum) || (s.exclusiveMinimum !== undefined && n <= s.exclusiveMinimum)) throw new Error(`${key} is outside its permitted range.`);
      result[key] = n;
    } else result[key] = typeof value === 'string' ? value.trim() : value;
    if (s.format === 'uuid' && !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(result[key])) throw new Error(`${key} must be a valid record ID.`);
  }
  return result;
}
function FormFields({ schema, values, change, fixed = {}, options = {}, prefix = '' }: { schema: Schema; values: Values; change: (v: Values) => void; fixed?: Values; options?: Options; prefix?: string }) {
 return <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{Object.entries(schema.properties || {}).filter(([key]) => key !== 'idempotency_key' && !(key in fixed)).map(([key, original]) => {
  const s=resolve(original), label=key.replace(/_/g,' '), name=`${prefix}${label}`, required=!!schema.required?.includes(key), value=values[key] ?? '';
  const update=(v: unknown)=>change({...values,[key]:v});
  if(s.type==='array') return <fieldset key={key} className="sm:col-span-2 space-y-3 border border-slate-700 p-3"><legend>{label}</legend>{value.map((item: Values,index: number)=><div key={index} className="space-y-2"><FormFields schema={resolve(s.items!)} values={item} change={v=>update(value.map((old: Values,i: number)=>i===index?v:old))} options={options} prefix={`${label} ${index+1} `}/><button type="button" className={buttonClass} disabled={value.length<=(s.minItems || 1)} onClick={()=>update(value.filter((_: unknown,i: number)=>i!==index))}>Remove line {index+1}</button></div>)}<button type="button" className={buttonClass} disabled={value.length>=(s.maxItems || 100)} onClick={()=>update([...value,initial(resolve(s.items!),{})])}>Add line</button></fieldset>;
  const choices=options[key] || s.enum?.map(v=>({value:String(v),label:String(v)}));
  return <label key={key} className="text-xs space-y-1"><span className="block">{name}{required?' *':''}</span>{choices ? <select aria-label={name} required={required} className={controlClass} value={String(value)} onChange={e=>update(e.target.value)}><option value="">Select {label}</option>{choices.map(c=><option key={c.value} value={c.value}>{c.label}</option>)}</select> : s.type==='boolean' ? <input aria-label={name} type="checkbox" checked={!!value} onChange={e=>update(e.target.checked)}/> : <input aria-label={name} className={controlClass} required={required} value={String(value)} onChange={e=>update(e.target.value)} type={s.format==='date'?'date':s.format==='date-time'?'datetime-local':s.type==='number'||s.type==='integer'?'number':'text'} min={s.minimum ?? (s.exclusiveMinimum!==undefined?s.exclusiveMinimum+(s.type==='integer'?1:0.000001):undefined)} max={s.maximum} step={s.type==='integer'?1:'any'} minLength={s.minLength} maxLength={s.maxLength} />}</label>;
 })}</div>;
}

export interface MutationFormProps {
 title: string; path: string; method?: 'POST'|'PUT'|'PATCH'|'DELETE'; schema?: keyof typeof mutationSchemas;
 permission: string; global?: boolean; also?: string[]; fixed?: Values; defaults?: Values; options?: Options;
 confirm?: string; validate?: (body: Values) => string | undefined; onSuccess?: (result: any) => void; description?: string;
}
/** A submitted intent keeps its backend idempotency key across retries/remounts.
 * Unknown outcomes without backend idempotency stop automatic resubmission. */
export function MutationForm(props: MutationFormProps) {
 const allowed=useCapability(props.permission,props.global); const user=useAuthStore(s=>s.user);
 const [open,setOpen]=useState(false);
 if(!allowed || props.also?.some(p=>!user?.backendPermissions?.includes(p))) return null;
 return <><button className={buttonClass} onClick={()=>setOpen(true)}>{props.title}</button>{open&&<MutationDialog key={`${props.path}-${JSON.stringify(props.fixed)}`} {...props} close={()=>setOpen(false)}/>}</>;
}
function MutationDialog(props: MutationFormProps & {close:()=>void}) {
 const schema=props.schema?schemas[props.schema]:{properties:{}}; const fixed=props.fixed || {};
 const cache=useQueryClient(); const user=useAuthStore(s=>s.user); const locked=useRef(false);
 const storageKey=`sanjeevani:mutation:${user?.id}:${props.method || 'POST'}:${props.path}:${props.title}:${JSON.stringify(fixed)}`;
 const [saved]=useState<Values|null>(()=>{try{return JSON.parse(sessionStorage.getItem(storageKey)||'null');}catch{return null;}});
 const [values,setValues]=useState<Values>(()=>saved?.values || initial(schema,{...props.defaults,...fixed}));
 const [intent,setIntent]=useState<Values|null>(saved); const [busy,setBusy]=useState(false); const [error,setError]=useState<Error|null>(null);
 const [review,setReview]=useState<Values|null>(null); const [done,setDone]=useState(false); const [uncertain,setUncertain]=useState(!!saved);
 const idempotent=!!schema.properties?.idempotency_key;
 function prepare() {try {const body={...payloadFor(schema,values),...fixed}; const invalid=props.validate?.(body); if(invalid)throw new Error(invalid); setError(null); if(props.confirm)setReview(body);else void execute(body);}catch(e){setError(new ApiError((e as Error).message,422));}}
 async function execute(body: Values) {
  if(locked.current || done || (uncertain&&!idempotent)) return;
  if(!user?.backendPermissions?.includes(props.permission) || props.also?.some(p=>!user.backendPermissions?.includes(p))) {setError(new ApiError('Permission denied.',403));return;}
  locked.current=true;setBusy(true);setError(null);
  const request=intent || {body:idempotent?{...body,idempotency_key:crypto.randomUUID()}:body,values};
  setIntent(request);sessionStorage.setItem(storageKey,JSON.stringify(request));
  try {
   const result=await sendData(props.path,props.method || 'POST',request.body);
   // A confirmed write is never retried because a later refresh fails.
   setDone(true);setUncertain(false);sessionStorage.removeItem(storageKey);setReview(null);
   await cache.invalidateQueries({queryKey:['backend']}); props.onSuccess?.(result);
  } catch(e) {
   setError(e instanceof Error?e:new Error('Request failed.'));
   const unknown=!(e instanceof ApiError) || e.status===0 || e.status>=500;
   setUncertain(unknown);
   if(!unknown) {setIntent(null);sessionStorage.removeItem(storageKey);}
   if(e instanceof ApiError && e.status===409) await cache.invalidateQueries({queryKey:['backend']});
  } finally {locked.current=false;setBusy(false);}
 }
 return <Modal isOpen title={props.title} onClose={()=>{if(!locked.current)props.close();}} maxWidth="2xl"><div className="max-h-[75vh] overflow-y-auto space-y-4">
  {props.description&&<p className="text-sm">{props.description}</p>}{Object.keys(fixed).length>0&&<Fields value={fixed}/>}
  {error&&<DataError error={error}/>}
  {done?<p role="status">Backend confirmed {props.title.toLowerCase()}. {busy?'Refreshing data...':'Data refreshed; any refresh error is shown on the underlying screen.'}</p>:<form onSubmit={e=>{e.preventDefault();prepare();}} className="space-y-4"><fieldset disabled={busy||uncertain||!!review}><FormFields schema={schema} values={values} change={setValues} fixed={fixed} options={props.options}/></fieldset>
  {uncertain&&<p role="alert">The previous request may have committed. {idempotent?'Retry uses the same payload and idempotency key.':'Refresh and check existing records before starting another action; the backend has no idempotency key for this operation.'}</p>}
  {review&&<div role="region" aria-label="Confirm operational change" className="space-y-3 border border-amber-500 p-3"><p>{props.confirm}</p><Fields value={review}/><button type="button" className={buttonClass} disabled={busy || (uncertain&&!idempotent)} onClick={()=>execute(review)}>{busy?'Saving...':'Confirm change'}</button><button type="button" className={buttonClass} disabled={busy||uncertain} onClick={()=>setReview(null)}>Back</button></div>}
  {!review&&<button className={buttonClass} disabled={busy || (uncertain&&!idempotent)}>{busy?'Saving...':props.confirm?'Review change':uncertain?'Retry same request':'Save'}</button>}
  </form>}
  {(done||uncertain)&&<button type="button" className={buttonClass} disabled={busy} onClick={()=>{sessionStorage.removeItem(storageKey);props.close();}}>Close {uncertain?'after checking records':'completed action'}</button>}
 </div></Modal>;
}
