import { apiRequest, ApiError } from './httpClient';

export type QueryParams = Record<string, string | number | boolean | undefined | null>;
export function apiPath(path: string, params: QueryParams = {}): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
  });
  return `/api/v1${path}${query.size ? `?${query}` : ''}`;
}
export async function getData<T>(path: string, params: QueryParams = {}): Promise<T> {
  const result = await apiRequest<{ success: true; data: T }>(apiPath(path, params));
  if (result?.success !== true || result.data === undefined) throw new ApiError('The backend returned an invalid data response.');
  return result.data;
}
export async function sendData<T>(path: string, method: 'POST' | 'PUT' | 'PATCH' | 'DELETE', body?: unknown): Promise<T> {
  const result = await apiRequest<{ success: true; data: T }>(apiPath(path), {
    method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (result?.success !== true || result.data === undefined) throw new ApiError('The backend returned an invalid data response.');
  return result.data;
}
/** Fetch a complete directory, never present the first API page as the total. */
export async function getDirectory<T>(path: string, params: QueryParams = {}): Promise<T[]> {
  const rows: T[] = [];
  for (let offset = 0; offset < 20000; offset += 200) {
    const page = await getData<T[]>(path, { ...params, offset, limit: 200 });
    if (!Array.isArray(page)) throw new ApiError('The backend returned an invalid list.');
    rows.push(...page);
    if (page.length < 200) return rows;
  }
  throw new ApiError('This directory exceeds the supported size. Narrow the geography or search filters.');
}
export async function downloadReport(kind: string, format: 'csv' | 'pdf' | 'xlsx', params: QueryParams): Promise<void> {
  return downloadFile(`/reports/${kind}`, `${kind}.${format}`, { ...params, format });
}
export async function downloadFile(path: string, filename: string, params: QueryParams = {}): Promise<void> {
  const blob = await apiRequest<Blob>(apiPath(path, params), {}, 'blob');
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = url; link.download = filename;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
