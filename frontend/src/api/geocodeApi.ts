/**
 * API client methods for geocode endpoint.
 */

import { request } from './client';
import { GeocodePlaceDTO } from './types';

export async function searchPlaces(
  q: string,
  signal?: AbortSignal,
): Promise<GeocodePlaceDTO[]> {
  const query = encodeURIComponent(q.trim());
  return request<GeocodePlaceDTO[]>(`/api/geocode/?q=${query}`, {
    method: 'GET',
    signal,
  });
}
