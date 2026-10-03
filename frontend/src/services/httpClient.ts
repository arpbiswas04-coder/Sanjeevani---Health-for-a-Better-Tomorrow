const BASE_URL = (import.meta.env.VITE_BACKEND_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')).replace(/\/$/, '');
export const SESSION_KEY = 'sanjeevani_auth_session';
export const SESSION_EVENT = 'sanjeevani:session';
export interface TokenPair { access_token: string; refresh_token: string; token_type: 'bearer'; expires_in: number }
interface Session { version: 1; accessToken: string; refreshToken: string; expiresAt: number; persistent: boolean }
export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message); }
}
let generation = 0;
let refreshing: Promise<Session> | null = null;

export function readSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw);
    if (value.version !== 1 || typeof value.accessToken !== 'string' || !value.accessToken ||
        typeof value.refreshToken !== 'string' || !value.refreshToken || !Number.isFinite(value.expiresAt)) return null;
    return value;
  } catch { return null; }
}
export function clearSession(): void {
  generation++;
  localStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(SESSION_KEY);
  window.dispatchEvent(new Event(SESSION_EVENT));
}
export function saveTokens(tokens: TokenPair, persistent: boolean): Session {
  if (!tokens?.access_token || !tokens.refresh_token || tokens.token_type !== 'bearer' || !(tokens.expires_in > 0))
    throw new ApiError('The backend returned an invalid authentication response.');
  const value: Session = { version: 1, accessToken: tokens.access_token, refreshToken: tokens.refresh_token,
    expiresAt: Date.now() + tokens.expires_in * 1000, persistent };
  localStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(SESSION_KEY);
  (persistent ? localStorage : sessionStorage).setItem(SESSION_KEY, JSON.stringify(value));
  window.dispatchEvent(new Event(SESSION_EVENT));
  return value;
}

export async function publicRequest<T>(path: string, options: RequestInit = {}, responseType: 'json' | 'blob' = 'json'): Promise<T> {
  if (!path.startsWith('/api/v1/')) throw new ApiError('Invalid API path.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${BASE_URL}${path}`, { ...options, signal: controller.signal, cache: 'no-store' });
    if (response.ok && responseType === 'blob') return await response.blob() as T;
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const message = response.status >= 500 ? 'Backend service or database unavailable. Please try again later.'
        : response.status === 422 ? `Request fields are missing or invalid. ${Array.isArray(body?.detail) ? body.detail.map((item: { loc?: string[]; msg?: string }) => `${item.loc?.slice(1).join('.')}: ${item.msg}`).join('; ') : body?.error?.message || 'Check the submitted values.'}`
        : response.status === 429 ? 'Too many attempts. Please wait before trying again.'
        : response.status === 403 ? 'Permission denied for this resource or facility.'
        : response.status === 404 ? body?.error?.message || 'The requested record was not found.'
        : response.status === 409 ? body?.error?.message || 'This record changed or the action conflicts with its current state. Refresh and try again.'
        : body?.error?.message || (response.status === 401 ? 'Invalid credentials or expired session.' : `Request failed (${response.status}).`);
      throw new ApiError(message, response.status);
    }
    if (body === null) throw new ApiError('The backend returned an invalid response.');
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Cannot reach the backend. Check your connection and try again.');
  } finally { clearTimeout(timer); }
}

async function refreshSession(): Promise<Session> {
  if (refreshing) return refreshing;
  const original = readSession();
  if (!original) throw new ApiError('Your session has expired. Please sign in again.', 401);
  const rotate = async () => {
    const revision = generation;
    const session = readSession();
    if (!session) throw new ApiError('Your session has expired. Please sign in again.', 401);
    // A different tab may have rotated while this tab waited for the lock.
    if (session.refreshToken !== original.refreshToken) return session;
    try {
      const result = await publicRequest<{ data: TokenPair }>('/api/v1/auth/refresh', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: session.refreshToken }),
      });
      if (generation !== revision) throw new ApiError('Session ended. Please sign in again.', 401);
      return saveTokens(result.data, session.persistent);
    } catch (error) {
      if (generation === revision) clearSession();
      throw error;
    }
  };
  const perform = async (): Promise<Session> => {
    if (navigator.locks) return await navigator.locks.request('sanjeevani-token-refresh', rotate);
    return await rotate();
  };
  const pending = perform().finally(() => { refreshing = null; });
  refreshing = pending;
  return pending;
}

/** Use for every protected backend request; retries once after rotating an expired token. */
export async function apiRequest<T>(path: string, options: RequestInit = {}, responseType: 'json' | 'blob' = 'json'): Promise<T> {
  let session = readSession();
  if (!session) { clearSession(); throw new ApiError('Please sign in to continue.', 401); }
  if (session.expiresAt <= Date.now() + 30000) session = await refreshSession();
  const revision = generation;
  const send = (token: string) => {
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    return publicRequest<T>(path, { ...options, headers }, responseType);
  };
  try { return await send(session.accessToken); }
  catch (error) {
    if (revision !== generation) throw new ApiError('Session changed. Please try again.', 401);
    if (!(error instanceof ApiError) || error.status !== 401) throw error;
    const latest = readSession();
    session = latest && latest.accessToken !== session.accessToken ? latest : await refreshSession();
    try { return await send(session.accessToken); }
    catch (retryError) {
      if (retryError instanceof ApiError && retryError.status === 401) clearSession();
      throw retryError;
    }
  }
}

window.addEventListener('storage', (event) => {
  if (event.key === SESSION_KEY || event.key === null) {
    generation++;
    window.dispatchEvent(new Event(SESSION_EVENT));
  }
});
