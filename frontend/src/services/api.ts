import { HealthStatus } from '@/types';

import { publicRequest } from './httpClient';
export { apiRequest } from './httpClient';

export async function fetchHealth(): Promise<HealthStatus> {
  return publicRequest<HealthStatus>('/api/v1/health');
}
