// Common shared types for Sanjeevani Grid Frontend

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical';

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string | null;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

export * from './auth';

export interface HealthStatus {
  status: string;
  service: string;
}
