import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { useTripHeatmap } from './useTripHeatmap';
import * as tripsApi from '../api/tripsApi';
import { TripHeatmapResponse, TripRequestPayload } from '../api/types';

describe('useTripHeatmap', () => {
  const mockPayloadA: TripRequestPayload = {
    origin: { label: 'Dallas, TX', lat: 32.7767, lon: -96.797 },
    destination: { label: 'Denver, CO', lat: 39.7392, lon: -104.9903 },
    departure_local: '2026-10-12T08:00',
    load_weight_lb: 45000,
    interval: 'auto',
  };

  const mockPayloadB: TripRequestPayload = {
    ...mockPayloadA,
    load_weight_lb: 10000,
  };

  const mockResponse: TripHeatmapResponse = {
    start_utc: '2026-10-12T13:00:00Z',
    start_local: '2026-10-12T08:00',
    origin_timezone: 'America/Chicago',
    cells: [],
    frames: [],
  };

  it('includes load_weight_lb in query and triggers new fetch when load changes', async () => {
    const getTripHeatmapSpy = vi
      .spyOn(tripsApi, 'getTripHeatmap')
      .mockResolvedValue(mockResponse);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result, rerender } = renderHook(
      ({ payload }) => useTripHeatmap(payload),
      {
        initialProps: { payload: mockPayloadA },
        wrapper,
      },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(getTripHeatmapSpy).toHaveBeenCalledTimes(1);
    expect(getTripHeatmapSpy).toHaveBeenLastCalledWith(mockPayloadA, expect.anything());

    // Rerender with different load weight
    rerender({ payload: mockPayloadB });

    await waitFor(() => expect(getTripHeatmapSpy).toHaveBeenCalledTimes(2));
    expect(getTripHeatmapSpy).toHaveBeenLastCalledWith(mockPayloadB, expect.anything());

    getTripHeatmapSpy.mockRestore();
  });
});
