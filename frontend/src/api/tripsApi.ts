/**
 * API client methods for trips endpoints.
 */

import { request } from './client';
import { AnalyzeResponse, TripRequestPayload } from './types';

export async function analyzeTrip(
  input: TripRequestPayload,
  signal?: AbortSignal,
): Promise<AnalyzeResponse> {
  return request<AnalyzeResponse>('/api/trips/analyze/', {
    method: 'POST',
    body: JSON.stringify(input),
    signal,
  });
}
