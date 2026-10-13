import { useQuery } from '@tanstack/react-query';
import { getTripHeatmap } from '../api/tripsApi';
import { TripHeatmapResponse, TripRequestPayload } from '../api/types';

/**
 * Hook to fetch 49-frame corridor risk heatmap for a trip.
 */
export function useTripHeatmap(payload: TripRequestPayload | null) {
  return useQuery<TripHeatmapResponse>({
    queryKey: [
      'tripHeatmap',
      payload?.origin,
      payload?.destination,
      payload?.departure_local,
      payload?.load_weight_lb,
    ],
    queryFn: ({ signal }) => {
      if (!payload) {
        throw new Error('Trip request payload required');
      }
      return getTripHeatmap(payload, signal);
    },
    enabled: Boolean(
      payload &&
        payload.origin &&
        payload.destination &&
        payload.departure_local,
    ),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
