/**
 * Base HTTP client and typed request helpers.
 * Handles unified error mapping into AppError, 60s timeout, and health checks.
 */

import { useQuery } from '@tanstack/react-query';
import { ApiErrorEnvelope } from './types';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(
  /\/+$/,
  '',
);

export class AppError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields?: Record<string, string[]>;

  constructor(params: {
    message: string;
    status: number;
    code: string;
    fields?: Record<string, string[]>;
  }) {
    super(params.message);
    this.name = 'AppError';
    this.status = params.status;
    this.code = params.code;
    this.fields = params.fields;
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const timeoutMs = 60_000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let onCallerAbort: (() => void) | undefined;
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      onCallerAbort = () => controller.abort();
      options.signal.addEventListener('abort', onCallerAbort);
    }
  }

  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorBody: ApiErrorEnvelope | null = null;
      try {
        errorBody = (await response.json()) as ApiErrorEnvelope;
      } catch {
        // Non-JSON response
      }

      if (errorBody && errorBody.error) {
        const normalizedFields: Record<string, string[]> = {};
        if (errorBody.error.fields) {
          for (const [key, val] of Object.entries(errorBody.error.fields)) {
            normalizedFields[key] = Array.isArray(val) ? val : [String(val)];
          }
        }

        throw new AppError({
          status: response.status,
          code: errorBody.error.code || 'api_error',
          message:
            errorBody.error.message ||
            `Request failed with status ${response.status}`,
          fields:
            Object.keys(normalizedFields).length > 0
              ? normalizedFields
              : undefined,
        });
      }

      throw new AppError({
        status: response.status,
        code: response.status === 429 ? 'rate_limited' : 'api_error',
        message: `Request failed with HTTP ${response.status}`,
      });
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    if (err instanceof AppError) {
      throw err;
    }

    const isAbort = err instanceof DOMException && err.name === 'AbortError';
    if (isAbort) {
      // Check whether caller aborted or timeout fired
      if (options.signal?.aborted) {
        throw new AppError({
          status: 0,
          code: 'aborted',
          message: 'Request was cancelled.',
        });
      }
      throw new AppError({
        status: 408,
        code: 'request_timeout',
        message: 'Request timed out after 60 seconds.',
      });
    }

    throw new AppError({
      status: 0,
      code: 'network_error',
      message:
        err instanceof Error && err.message
          ? err.message
          : 'Network error: could not connect to server.',
    });
  } finally {
    clearTimeout(timeoutId);
    if (options.signal && onCallerAbort) {
      options.signal.removeEventListener('abort', onCallerAbort);
    }
  }
}

export interface HealthResponse {
  status: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health/');
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 1,
  });
}
