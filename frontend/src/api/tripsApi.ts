/**
 * API client methods for trips endpoints.
 */

import { request } from './client';
import { AnalyzeResponse, TripHeatmapResponse, TripRequestPayload } from './types';

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

export async function getTripHeatmap(
  input: TripRequestPayload,
  signal?: AbortSignal,
): Promise<TripHeatmapResponse> {
  return request<TripHeatmapResponse>('/api/trips/heatmap/', {
    method: 'POST',
    body: JSON.stringify(input),
    signal,
  });
}
