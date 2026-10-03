import React, { ReactNode, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { ApiError } from '@/services/httpClient';
import { QueryParams } from '@/services/dataApi';
import { useBackendData } from '@/hooks/useBackendData';

export const controlClass = 'bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200';
export const buttonClass = 'px-3 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs disabled:opacity-40 hover:bg-slate-700';
export function PageHeading({ title, description }: { title: string; description: string }) {
  return <header><h2 className="text-2xl font-bold tracking-tight text-slate-100">{title}</h2><p className="text-xs text-slate-400 mt-1">{description}</p></header>;
}
export function Unavailable({ children }: { children: ReactNode }) {
  return <p className="text-xs text-slate-400 p-4 border border-dashed border-slate-700 rounded-xl">Unavailable: {children}</p>;
}
export function DataError({ error }: { error: Error }) {
  const status = error instanceof ApiError ? error.status : 0;
  const label = status === 400 ? 'INVALID_REQUEST' : status === 429 ? 'RATE_LIMITED' : status === 401 ? 'UNAUTHORIZED' : status === 403 ? 'FORBIDDEN' : status === 422 ? 'VALIDATION_ERROR'
    : status >= 500 ? 'BACKEND_UNAVAILABLE' : status === 404 ? 'NOT_FOUND' : status === 409 ? 'CONFLICT' : 'NETWORK_ERROR';
  return <p role="alert" data-state={label} className="text-xs text-rose-300 p-3 border border-rose-500/30 rounded-xl">{error.message}</p>;
}
export type DataQuery<T> = { data?: T; error: Error | null; isPending: boolean; waiting?: boolean; isFetching: boolean; refetch: () => unknown };
export function DataState<T>({ query, empty = false, children }: { query: DataQuery<T>; empty?: boolean; children: ReactNode }) {
  if (query.error) return <DataError error={query.error} />;
  if (query.waiting) return <p role="status" className="text-xs text-slate-400">Select the required facility or record.</p>;
  if (query.isPending) return <p role="status" data-state="LOADING" className="text-xs text-slate-400">Loading backend data…</p>;
  if (empty) return <p role="status" data-state="SUCCESS_EMPTY" className="text-xs text-slate-400">No records in your permitted scope for these filters.</p>;
  return <div data-state="SUCCESS_WITH_DATA">{children}</div>;
}
export interface Column { key: string; label: string; render?: (row: Record<string, unknown>) => ReactNode }
export function displayValue(value: unknown): string {
  if (value === null || value === undefined) return 'Not recorded';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
export function RecordTable({ rows, columns, onSelect }: { rows: object[]; columns: Column[]; onSelect?: (row: Record<string, unknown>) => void }) {
  return <div className="overflow-x-auto"><table className="w-full text-xs text-left"><thead className="text-slate-400 border-b border-slate-800"><tr>{columns.map(c => <th className="p-3" key={c.key}>{c.label}</th>)}{onSelect && <th>Details</th>}</tr></thead>
    <tbody>{rows.map((item, i) => { const row = item as Record<string, unknown>; return <tr key={String(row.id ?? i)} className="border-b border-slate-800/60 text-slate-200">{columns.map(c => <td className="p-3 max-w-xs break-words" key={c.key}>{c.render ? c.render(row) : displayValue(row[c.key])}</td>)}{onSelect && <td><button className={buttonClass} onClick={() => onSelect(row)}>View details</button></td>}</tr>; })}</tbody></table></div>;
}
export function Fields({ value }: { value: object }) {
  return <dl className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">{Object.entries(value).map(([key, item]) => <div key={key}><dt className="text-slate-400">{key.replace(/_/g, ' ')}</dt><dd className="text-slate-200 break-words">{displayValue(item)}</dd></div>)}</dl>;
}
/** Each panel owns its request, failure and pagination; sibling panels stay usable. */
export function DataPanel({ title, path, params = {}, permission, columns, enabled = true, paginated = true, onSelect }: {
  title: string; path: string; params?: QueryParams; permission?: string; columns: Column[]; enabled?: boolean; paginated?: boolean; onSelect?: (row: Record<string, unknown>) => void;
}) {
  const [offset, setOffset] = useState(0);
  const query = useBackendData<object[]>(path, { ...params, ...(paginated ? { offset, limit: 50 } : {}) }, permission, enabled);
  return <Card className="space-y-4"><div className="flex justify-between gap-3"><h3 className="font-bold text-sm text-slate-100">{title}</h3><button className={buttonClass} disabled={query.isFetching || query.waiting || !!query.error && query.error instanceof ApiError && query.error.status === 403} onClick={() => query.refetch()}>Refresh {title}</button></div>
    <DataState query={query} empty={query.data?.length === 0}><RecordTable rows={query.data || []} columns={columns} onSelect={onSelect} /></DataState>
    {paginated && <div className="flex items-center gap-3 text-xs text-slate-400"><button className={buttonClass} disabled={!offset || query.isFetching} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</button><span>Page {offset / 50 + 1} · up to 50 records</span><button className={buttonClass} disabled={query.isFetching || query.data?.length !== 50} onClick={() => setOffset(offset + 50)}>Next</button></div>}
  </Card>;
}
export function DetailPanel({ title, path, permission }: { title: string; path: string; permission?: string }) {
  const query = useBackendData<object>(path, {}, permission);
  return <Card className="space-y-3"><h3 className="font-bold text-sm text-slate-100">{title}</h3><DataState query={query}>{query.data && <Fields value={query.data} />}</DataState></Card>;
}
