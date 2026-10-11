import { useMutation } from '@tanstack/react-query';
import { AppError } from '../api/client';
import { analyzeTrip } from '../api/tripsApi';
import { AnalyzeResponse, TripRequestPayload } from '../api/types';

/**
 * Trip analysis mutation hook.
 */
export function useAnalyzeTrip() {
  return useMutation<AnalyzeResponse, AppError, TripRequestPayload>({
    mutationFn: (payload: TripRequestPayload) => analyzeTrip(payload),
  });
}
