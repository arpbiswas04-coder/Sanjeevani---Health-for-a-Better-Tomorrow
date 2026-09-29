import { HealthStatus } from '@/types';

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${BASE_URL}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}
