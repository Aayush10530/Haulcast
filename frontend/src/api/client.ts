import { useQuery } from '@tanstack/react-query';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(
  /\/+$/,
  '',
);

export interface HealthResponse {
  status: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const url = `${API_BASE_URL}/api/health/`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check failed with HTTP ${response.status}`);
  }
  return response.json();
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 1,
  });
}
